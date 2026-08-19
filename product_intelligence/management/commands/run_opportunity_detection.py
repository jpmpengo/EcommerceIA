
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

from product_intelligence.services.etsy_client import (
    EtsyClient,
)
from product_intelligence.services.etsy_market_observation import (
    EtsyMarketObservationService,
)

from product_intelligence.services.cj_supplier_searcher import (
    CJSupplierSearcher,
)
from product_intelligence.services.market_opportunity_pipeline import (
    MarketOpportunityPipelineService,
)
from product_intelligence.services.multi_supplier_search import (
    MultiSupplierSearchService,
)
from product_intelligence.services.printful_client import (
    PrintfulClient,
)
from product_intelligence.services.printful_supplier_offer import (
    PrintfulSupplierOfferService,
)
from product_intelligence.services.printful_supplier_searcher import (
    PrintfulSupplierSearcher,
)
from product_intelligence.services.supplier_offer_comparison import (
    SupplierOfferComparisonService,
)
from product_intelligence.services.supplier_product_matching import (
    SupplierProductMatchingService,
)
from product_intelligence.services.supplier_selection import (
    SupplierSelectionService,
)


class Command(BaseCommand):
    help = (
        "Processes eBay, Etsy and WooCommerce market observations "
        "and detects CJdropshipping product opportunities."
    )

    def handle(self, *args, **options):
        api_key = os.getenv("CJ_API_KEY")

        printful_api_token = os.getenv(
            "PRINTFUL_API_TOKEN"
        )

        use_multi_supplier_pipeline = (
            os.getenv(
                "USE_MULTI_SUPPLIER_PIPELINE"
            )
            == "1"
        )

        if (
            use_multi_supplier_pipeline
            and not printful_api_token
        ):
            raise CommandError(
                "PRINTFUL_API_TOKEN is missing."
            )

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

        etsy_api_key = os.getenv(
            "ETSY_API_KEY"
        )
        etsy_shared_secret = os.getenv(
            "ETSY_SHARED_SECRET"
        )
        etsy_listing_ids_raw = os.getenv(
            "ETSY_LISTING_IDS",
            "",
        )

        try:
            etsy_listing_ids = [
                int(value.strip())
                for value in etsy_listing_ids_raw.split(",")
                if value.strip()
            ]
        except ValueError as exc:
            raise CommandError(
                "ETSY_LISTING_IDS must contain comma-separated integers."
            ) from exc

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

        if (
            etsy_api_key
            and etsy_shared_secret
            and etsy_listing_ids
        ):
            etsy_ssl_context = truststore.SSLContext(
                ssl.PROTOCOL_TLS_CLIENT
            )

            with httpx.Client(
                verify=etsy_ssl_context,
                timeout=30.0,
            ) as etsy_http_client:
                etsy_client = EtsyClient(
                    api_key=etsy_api_key,
                    shared_secret=etsy_shared_secret,
                    http_client=etsy_http_client,
                )

                observation_service = (
                    EtsyMarketObservationService()
                )

                for listing_id in etsy_listing_ids:
                    listing = etsy_client.get_listing(
                        listing_id=listing_id,
                    )

                    normalized_listing = (
                        etsy_client.normalize_listing(
                            listing
                        )
                    )

                    observation_service.create_observation(
                        listing=normalized_listing,
                    )

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

            if use_multi_supplier_pipeline:
                printful_supplier, _ = (
                    Supplier.objects.get_or_create(
                        name="Printful",
                        defaults={
                            "country": "US",
                            "website": (
                                "https://www.printful.com"
                            ),
                            "supplier_type": (
                                "print_on_demand"
                            ),
                        },
                    )
                )

                printful_client = PrintfulClient(
                    api_token=printful_api_token,
                    http_client=http_client,
                )

                matching_service = (
                    SupplierProductMatchingService()
                )

                currency_conversion_service = (
                    CurrencyConversionService()
                )

                selection_service = (
                    SupplierSelectionService(
                        currency_conversion_service=(
                            currency_conversion_service
                        ),
                        exchange_rate_client=(
                            exchange_rate_client
                        ),
                    )
                )

                comparison_service = (
                    SupplierOfferComparisonService(
                        matching_service=(
                            matching_service
                        ),
                        selection_service=(
                            selection_service
                        ),
                    )
                )

                cj_searcher = CJSupplierSearcher(
                    client=cj_client,
                    supplier=supplier,
                    offer_service=(
                        CJSupplierOfferService()
                    ),
                )

                printful_searcher = (
                    PrintfulSupplierSearcher(
                        client=printful_client,
                        supplier=printful_supplier,
                        offer_service=(
                            PrintfulSupplierOfferService()
                        ),
                        matching_service=(
                            matching_service
                        ),
                    )
                )

                supplier_search_service = (
                    MultiSupplierSearchService(
                        supplier_searchers=[
                            cj_searcher,
                            printful_searcher,
                        ],
                    )
                )

                decision_service = (
                    OpportunityDecisionService(
                        minimum_score=minimum_score,
                    )
                )

                opportunity_service = (
                    SupplierOfferOpportunityService(
                        minimum_margin=minimum_margin,
                        minimum_score=minimum_score,
                        minimum_stock=minimum_stock,
                        decision_service=(
                            decision_service
                        ),
                    )
                )

                market_pipeline = (
                    MarketOpportunityPipelineService(
                        supplier_search_service=(
                            supplier_search_service
                        ),
                        comparison_service=(
                            comparison_service
                        ),
                        opportunity_service=(
                            opportunity_service
                        ),
                        currency_conversion_service=(
                            currency_conversion_service
                        ),
                        exchange_rate_client=(
                            exchange_rate_client
                        ),
                    )
                )

                for observation in observations:
                    market_pipeline.process(
                        market_observation=(
                            observation
                        ),
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        "Multi-supplier opportunity "
                        "detection completed."
                    )
                )

                return

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
    
                