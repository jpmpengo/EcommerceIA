import os
import ssl

import httpx
import truststore

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.services.etsy_client import EtsyClient


class Command(BaseCommand):
    help = "Teste les identifiants réels de l'API Etsy."

    def handle(self, *args, **options):
        api_key = os.getenv("ETSY_API_KEY")
        shared_secret = os.getenv("ETSY_SHARED_SECRET")

        if not api_key:
            raise CommandError(
                "ETSY_API_KEY is missing."
            )

        if not shared_secret:
            raise CommandError(
                "ETSY_SHARED_SECRET is missing."
            )

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        try:
            with httpx.Client(
                verify=ssl_context,
                timeout=30.0,
            ) as http_client:

                client = EtsyClient(
                    api_key=api_key,
                    shared_secret=shared_secret,
                    http_client=http_client,
                )

                result = client.ping()

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            self.stderr.write(
                f"Etsy response: {exc.response.text}"
            )

            raise CommandError(
                f"Etsy API returned HTTP {status_code}."
            ) from exc

        except Exception as exc:
            raise CommandError(
                f"Etsy API request failed: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Etsy API ping successful."
            )
        )

        application_id = result.get(
            "application_id"
        )

        self.stdout.write(
            f"Application ID present: "
            f"{application_id is not None}"
        )

