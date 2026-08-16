import os
import ssl

import httpx
import truststore

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)
from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient
from product_intelligence.services.cj_pipeline import CJPipelineService
from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)
from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)
from product_intelligence.services.ebay_cj_bridge import (
    EbayCJBridgeService,
)
from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)


class Command(BaseCommand):
    help = (
        "Teste la jonction réelle entre une MarketObservation eBay "
        "existante et CJdropshipping."
    )

    def handle(self, *args, **options):
        api_key = os.getenv("CJ_API_KEY")

        if not api_key:
            raise CommandError(
                "CJ_API_KEY is missing."
            )

        observation = (
            MarketObservation.objects
            .filter(source="ebay")
            .order_by("-observed_at")
            .first()
        )

        if observation is None:
            raise CommandError(
                "No eBay MarketObservation found in database."
            )

        if observation.observed_price is None:
            raise CommandError(
                "Latest eBay MarketObservation has no price."
            )

        supplier, _ = Supplier.objects.get_or_create(
            name="CJdropshipping",
            defaults={
                "country": "CN",
                "website": "https://cjdropshipping.com",
                "supplier_type": "dropshipper",
            },
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

            access_token = auth_client.get_access_token()

            cj_client = CJClient(
                access_token=access_token,
                http_client=http_client,
            )

            exchange_rate_client = ExchangeRateClient(
                http_client=http_client,
            )

            cj_pipeline = CJPipelineService(
                client=cj_client,
                offer_service=CJSupplierOfferService(),
                opportunity_service=(
                    SupplierOfferOpportunityService()
                ),
                currency_conversion_service=(
                    CurrencyConversionService()
                ),
                exchange_rate_client=(
                    exchange_rate_client
                ),
            )

            bridge = EbayCJBridgeService(
                cj_pipeline_service=cj_pipeline,
                cj_client=cj_client,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "Using eBay MarketObservation:"
                )
            )

            self.stdout.write(
                f"Observation ID: {observation.id}"
            )

            self.stdout.write(
                f"Name: {observation.name}"
            )

            self.stdout.write(
                f"Market price: "
                f"{observation.observed_price} "
                f"{observation.currency}"
            )

            opportunity = bridge.search_and_create_opportunity(
                market_observation=observation,
                supplier=supplier,
            )

            offer = (
                supplier.offers
                .filter(
                    market_observation=observation,
                )
                .order_by("-observed_at")
                .first()
            )

        if offer is None:
            raise CommandError(
                "SupplierOffer was not created."
            )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "eBay -> CJ bridge completed successfully."
            )
        )

        self.stdout.write(
            f"SupplierOffer ID: {offer.id}"
        )

        self.stdout.write(
            f"Supplier price: "
            f"{offer.purchase_price} "
            f"{offer.currency}"
        )

        self.stdout.write(
            f"Stock: {offer.stock}"
        )

        self.stdout.write(
            f"ProductOpportunity ID: "
            f"{opportunity.id}"
        )

        self.stdout.write(
            f"Opportunity supplier price: "
            f"{opportunity.supplier_price}"
        )

        self.stdout.write(
            f"Opportunity market price: "
            f"{opportunity.market_price}"
        )

        self.stdout.write(
            f"Opportunity margin: "
            f"{opportunity.get_estimated_margin()}"
        )

        self.stdout.write(
            f"Opportunity score: "
            f"{opportunity.opportunity_score}"
        )

        