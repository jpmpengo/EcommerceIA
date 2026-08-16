
import os

from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from woocommerce import API


class Command(BaseCommand):
    help = "Teste la connexion réelle à l'API WooCommerce."

    def handle(self, *args, **options):
        base_url = os.getenv("WOOCOMMERCE_BASE_URL")
        consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
        consumer_secret = os.getenv(
            "WOOCOMMERCE_CONSUMER_SECRET"
        )

        if not base_url:
            raise CommandError(
                "WOOCOMMERCE_BASE_URL is missing."
            )

        if not consumer_key:
            raise CommandError(
                "WOOCOMMERCE_CONSUMER_KEY is missing."
            )

        if not consumer_secret:
            raise CommandError(
                "WOOCOMMERCE_CONSUMER_SECRET is missing."
            )

        try:
            wcapi = API(
                url=base_url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3",
                wp_api=True,
                timeout=30,
            )

            response = wcapi.get("products")

        except Exception as exc:
            raise CommandError(
                f"WooCommerce API request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            raise CommandError(
                "WooCommerce API returned "
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

        products = response.json()

        self.stdout.write(
            self.style.SUCCESS(
                "WooCommerce API request successful."
            )
        )

        self.stdout.write(
            f"Products returned: {len(products)}"
        )
        