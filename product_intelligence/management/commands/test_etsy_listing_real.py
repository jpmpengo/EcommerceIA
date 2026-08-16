import os
import ssl

import httpx
import truststore

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from product_intelligence.services.etsy_client import (
    EtsyClient,
)

from product_intelligence.services.etsy_market_observation import (
    EtsyMarketObservationService,
)


class Command(BaseCommand):
    help = "Teste la récupération réelle d'un listing Etsy."

    def add_arguments(self, parser):
        parser.add_argument(
            "listing_id",
            type=int,
        )

    def handle(self, *args, **options):
        api_key = os.getenv("ETSY_API_KEY")
        shared_secret = os.getenv(
            "ETSY_SHARED_SECRET"
        )

        if not api_key:
            raise CommandError(
                "ETSY_API_KEY is missing."
            )

        if not shared_secret:
            raise CommandError(
                "ETSY_SHARED_SECRET is missing."
            )

        listing_id = options["listing_id"]

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        with httpx.Client(
            verify=ssl_context,
            timeout=30.0,
        ) as http_client:
            client = EtsyClient(
                api_key=api_key,
                shared_secret=shared_secret,
                http_client=http_client,
            )

            try:
                listing = client.get_listing(
                    listing_id=listing_id,
                )
            except httpx.HTTPStatusError as exc:
                raise CommandError(
                    "Etsy API returned "
                    f"HTTP {exc.response.status_code}: "
                    f"{exc.response.text}"
                ) from exc

            normalized = client.normalize_listing(
                listing
            )
            
            observation_service = EtsyMarketObservationService()

            observation = observation_service.create_observation(
                listing=normalized,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Etsy listing retrieved successfully."
            )
        )

        self.stdout.write(
            f"Listing ID: {normalized['external_id']}"
        )

        self.stdout.write(
            f"Name: {normalized['name']}"
        )

        self.stdout.write(
            f"Price: {normalized['observed_price']}"
        )

        self.stdout.write(
            f"Currency: {normalized['currency']}"
        )

        self.stdout.write(
            f"URL: {normalized['product_url']}"
        )

        self.stdout.write(
            f"MarketObservation ID: {observation.id}"
        )

        self.stdout.write(
            f"Source: {observation.source}"
        )

