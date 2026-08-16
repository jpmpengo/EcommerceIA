import os
import ssl

import httpx
import truststore

from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from woocommerce import API

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)
from product_intelligence.services.cj_auth_client import (
    CJAuthClient,
)
from product_intelligence.services.cj_client import (
    CJClient,
)
from product_intelligence.services.cj_pipeline import (
    CJPipelineService,
)
from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)
from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)
from product_intelligence.services.ebay_cj_bridge import (
    EbayCJBridgeService,
)
from product_intelligence.services.etsy_cj_bridge import (
    EtsyCJBridgeService,
)
from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)
from product_intelligence.services.opportunity_detection import (
    OpportunityDetectionService,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)
from product_intelligence.services.woocommerce_cj_bridge import (
    WooCommerceCJBridgeService,
)
from product_intelligence.services.woocommerce_client import (
    WooCommerceClient,
)
from product_intelligence.services.woocommerce_collection import (
    WooCommerceCollectionService,
)
from product_intelligence.services.woocommerce_market_observation import (
    WooCommerceMarketObservationService,
)

from decimal import Decimal, InvalidOperation

from product_intelligence.services.opportunity_decision import (
    OpportunityDecisionService,
)


class Command(BaseCommand):
    help = (
        "Processes eBay, Etsy and WooCommerce market observations "
        "and detects CJdropshipping product opportunities."
    )

    def handle(self, *args, **options):
        api_key = os.getenv("CJ_API_KEY")

        minimum_margin_raw = os.getenv(
            "OPPORTUNITY_MINIMUM_MARGIN"
        )

        minimum_margin = None

        if minimum_margin_raw:
            try:
                minimum_margin = Decimal(
                    minimum_margin_raw
                )
            except InvalidOperation as exc:
                raise CommandError(
                    "OPPORTUNITY_MINIMUM_MARGIN must be a valid decimal."
                ) from exc
            
        minimum_score_raw = os.getenv(
            "OPPORTUNITY_MINIMUM_SCORE"
        )
        
        minimum_score_raw = os.getenv(
            "OPPORTUNITY_MINIMUM_SCORE"
        )

        minimum_score = None

        if minimum_score_raw:
            try:
                minimum_score = int(
                minimum_score_raw
            )
            except ValueError as exc:
                raise CommandError(
                    "OPPORTUNITY_MINIMUM_SCORE must be a valid integer."
                ) from exc

            if not 0 <= minimum_score <= 100:
                raise CommandError(
                    "OPPORTUNITY_MINIMUM_SCORE must be between 0 and 100."
                )

        minimum_stock_raw = os.getenv(
            "OPPORTUNITY_MINIMUM_STOCK"
        )

        minimum_stock = None

        if minimum_stock_raw:
            try:
                minimum_stock = int(
                minimum_stock_raw
            )
            except ValueError as exc:
                raise CommandError(
                    "OPPORTUNITY_MINIMUM_STOCK must be a valid integer."
                ) from exc

            if minimum_stock < 0:
                raise CommandError(
                    "OPPORTUNITY_MINIMUM_STOCK must be zero or greater."
                )

        woocommerce_base_url = os.getenv(
            "WOOCOMMERCE_BASE_URL"
        )
        woocommerce_consumer_key = os.getenv(
            "WOOCOMMERCE_CONSUMER_KEY"
        )
        woocommerce_consumer_secret = os.getenv(
            "WOOCOMMERCE_CONSUMER_SECRET"
        )

        if not api_key:
            raise CommandError(
                "CJ_API_KEY is missing."
            )

        # Collecte WooCommerce uniquement si les 3 variables
        # de configuration sont présentes.
        if (
            woocommerce_base_url
            and woocommerce_consumer_key
            and woocommerce_consumer_secret
        ):
            wcapi = API(
                url=woocommerce_base_url,
                consumer_key=woocommerce_consumer_key,
                consumer_secret=woocommerce_consumer_secret,
                version="wc/v3",
                wp_api=True,
                timeout=30,
            )

            woocommerce_client = WooCommerceClient(
                api=wcapi,
            )

            woocommerce_collection_service = (
                WooCommerceCollectionService(
                    client=woocommerce_client,
                    observation_service=(
                        WooCommerceMarketObservationService()
                    ),
                )
            )

            woocommerce_collection_service.collect()

        observations = list(
            MarketObservation.objects
            .filter(
                source__in=[
                    "ebay",
                    "etsy",
                    "woocommerce",
                ]
            )
            .order_by("observed_at")
        )

        if not observations:
            self.stdout.write(
                self.style.WARNING(
                    "No eBay, Etsy or WooCommerce "
                    "MarketObservation found."
                )
            )
            return

        ebay_count = sum(
            1
            for observation in observations
            if observation.source == "ebay"
        )

        etsy_count = sum(
            1
            for observation in observations
            if observation.source == "etsy"
        )

        woocommerce_count = sum(
            1
            for observation in observations
            if observation.source == "woocommerce"
        )

        supplier, _ = Supplier.objects.get_or_create(
            name="CJdropshipping",
            defaults={
                "country": "CN",
                "website": "https://cjdropshipping.com",
                "supplier_type": "dropshipper",
            },
        )

        self.stdout.write(
            f"Market observations found: {len(observations)}"
        )

        self.stdout.write(
            f"eBay observations: {ebay_count}"
        )

        self.stdout.write(
            f"Etsy observations: {etsy_count}"
        )

        self.stdout.write(
            f"WooCommerce observations: {woocommerce_count}"
        )

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        with httpx.Client(
            verify=ssl_context,
            timeout=30.0,
        ) as http_client:

            auth_client = CJAuthClient(
                api_key=api_key,
                http_client=http_client,
            )

            access_token = (
                auth_client.get_access_token()
            )

            cj_client = CJClient(
                access_token=access_token,
                http_client=http_client,
            )

            exchange_rate_client = ExchangeRateClient(
                http_client=http_client,
            )

            decision_service = OpportunityDecisionService(
                minimum_score=minimum_score,
            )

            pipeline = CJPipelineService(
                client=cj_client,
                offer_service=CJSupplierOfferService(),
                opportunity_service=(
                    SupplierOfferOpportunityService(
                        minimum_margin=minimum_margin,
                        minimum_score=minimum_score,
                        minimum_stock=minimum_stock,
                        decision_service=decision_service,
                    )
                ),
                currency_conversion_service=(
                    CurrencyConversionService()
                ),
                exchange_rate_client=(
                    exchange_rate_client
                ),
            )

            ebay_bridge = EbayCJBridgeService(
                cj_pipeline_service=pipeline,
                cj_client=cj_client,
            )

            etsy_bridge = EtsyCJBridgeService(
                cj_pipeline_service=pipeline,
                cj_client=cj_client,
            )

            woocommerce_bridge = WooCommerceCJBridgeService(
                cj_pipeline_service=pipeline,
                cj_client=cj_client,
            )

            detection_service = (
                OpportunityDetectionService(
                    ebay_cj_bridge_service=ebay_bridge,
                    etsy_cj_bridge_service=etsy_bridge,
                    woocommerce_cj_bridge_service=woocommerce_bridge,
                )
            )

            summary = (
                detection_service
                .process_observations_with_summary(
                    market_observations=observations,
                    supplier=supplier,
                )
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Opportunity detection completed."
            )
        )

        self.stdout.write(
            f"Processed: {summary['processed']}"
        )

        self.stdout.write(
            f"Created: {summary['created']}"
        )

        self.stdout.write(
            "Skipped - no price: "
            f"{summary['skipped_no_price']}"
        )

        self.stdout.write(
            "Skipped - no CJ match: "
            f"{summary['skipped_no_match']}"
        )

        self.stdout.write(
            "Skipped - already processed: "
            f"{summary['skipped_already_processed']}"
        )

        if summary["results"]:
            self.stdout.write("")

            self.stdout.write(
                self.style.SUCCESS(
                    "Created opportunities:"
                )
            )

            for opportunity in summary["results"]:
                self.stdout.write(
                    f"  ID: {opportunity.id}"
                )

                self.stdout.write(
                    f"  Name: {opportunity.name}"
                )

                self.stdout.write(
                    "  Supplier price: "
                    f"{opportunity.supplier_price}"
                )

                self.stdout.write(
                    "  Market price: "
                    f"{opportunity.market_price}"
                )

                self.stdout.write(
                    "  Margin: "
                    f"{opportunity.get_estimated_margin()}"
                )

                self.stdout.write(
                    "  Score: "
                    f"{opportunity.opportunity_score}"
                )

                self.stdout.write("")
                
    
                