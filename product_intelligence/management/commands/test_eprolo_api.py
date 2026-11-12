import os
import ssl

import httpx
import truststore
from django.core.management.base import BaseCommand, CommandError

from product_intelligence.services.eprolo_client import EproloClient


class Command(BaseCommand):
    help = (
        "Vérifie le catalogue et les tarifs EPROLO "
        "en lecture seule."
    )

    def add_arguments(self, parser):
        parser.add_argument("--page", type=int, default=1)
        parser.add_argument("--product-id")
        parser.add_argument("--variant-id")
        parser.add_argument("--country", default="FR")

    def handle(self, *args, **options):
        api_key = os.getenv("EPROLO_API_KEY", "").strip()
        api_secret = os.getenv(
            "EPROLO_API_SECRET", ""
        ).strip()
        if not api_key or not api_secret:
            raise CommandError(
                "EPROLO_API_KEY ou EPROLO_API_SECRET absent."
            )

        with httpx.Client(
            verify=truststore.SSLContext(
                ssl.PROTOCOL_TLS_CLIENT
            ),
            timeout=60.0,
        ) as http_client:
            client = EproloClient(
                api_key=api_key,
                api_secret=api_secret,
                http_client=http_client,
                base_url=os.getenv(
                    "EPROLO_API_BASE_URL",
                    "",
                ) or None,
            )
            products = client.get_catalog_page(
                page=options["page"]
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"CATALOGUE EPROLO: {len(products)} produit(s)"
                )
            )
            for product in products[:5]:
                self.stdout.write(
                    f"- {product.get('id')} | "
                    f"{product.get('title')}"
                )

            product_id = options.get("product_id")
            variant_id = options.get("variant_id")
            if bool(product_id) != bool(variant_id):
                raise CommandError(
                    "Fournissez ensemble --product-id et --variant-id."
                )
            if product_id and variant_id:
                rates = client.get_shipping_rates(
                    product_id=product_id,
                    variant_id=variant_id,
                    destination_country=options["country"],
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"LIVRAISONS: {len(rates)} tarif(s)"
                    )
                )
                for rate in rates:
                    self.stdout.write(
                        "- {ship_method} | {cost} USD | {shiptime}".format(
                            **rate
                        )
                    )
