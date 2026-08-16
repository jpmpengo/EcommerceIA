import ssl

import httpx
import truststore

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)


class Command(BaseCommand):
    help = "Teste la récupération réelle du taux USD vers EUR."

    def handle(self, *args, **options):
        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        try:
            with httpx.Client(
                verify=ssl_context,
                timeout=30.0,
            ) as http_client:

                client = ExchangeRateClient(
                    http_client=http_client,
                )

                rate = client.get_rate(
                    from_currency="USD",
                    to_currency="EUR",
                )

        except Exception as exc:
            raise CommandError(
                f"Exchange rate request failed: {exc}"
            ) from exc

        if rate <= 0:
            raise CommandError(
                "Invalid USD/EUR exchange rate."
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Exchange rate request successful."
            )
        )

        self.stdout.write(
            f"USD -> EUR rate: {rate}"
        )

        