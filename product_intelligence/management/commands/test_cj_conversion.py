import os
import ssl
from decimal import Decimal

import httpx
import truststore

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient
from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)
from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)


class Command(BaseCommand):
    help = (
        "Teste en réel un prix de variante CJ, son stock "
        "et sa conversion USD vers EUR."
    )

    def handle(self, *args, **options):
        api_key = os.getenv("CJ_API_KEY")

        if not api_key:
            raise CommandError(
                "CJ_API_KEY is missing."
            )

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        with httpx.Client(
            verify=ssl_context,
            timeout=30.0,
        ) as http_client:

            # -----------------------------
            # Authentification CJ
            # -----------------------------

            auth_client = CJAuthClient(
                api_key=api_key,
                http_client=http_client,
            )

            access_token = auth_client.get_access_token()

            cj_client = CJClient(
                access_token=access_token,
                http_client=http_client,
            )

            # -----------------------------
            # Client de taux de change
            # -----------------------------

            exchange_rate_client = ExchangeRateClient(
                http_client=http_client,
            )

            conversion_service = CurrencyConversionService()

            # -----------------------------
            # Recherche CJ
            # -----------------------------

            products = cj_client.search_products(
                keyword="wireless charger",
            )

            if not products:
                raise CommandError(
                    "CJ returned no products."
                )

            selected_detail = None
            selected_variant = None

            # -----------------------------
            # Chercher une variante réelle
            # -----------------------------

            for index, product in enumerate(
                products,
                start=1,
            ):
                product_id = product.get("id")

                if not product_id:
                    continue

                self.stdout.write(
                    f"Checking product "
                    f"{index}/{len(products)}..."
                )

                detail = cj_client.get_product_detail(
                    product_id=product_id,
                )

                if not detail:
                    self.stdout.write(
                        "No detail returned. Skipping."
                    )
                    continue

                variants = detail.get("variants") or []

                if not variants:
                    continue

                for variant in variants:
                    variant_price = variant.get(
                        "variantSellPrice"
                    )

                    variant_id = variant.get("vid")

                    if (
                        variant_price is not None
                        and variant_id
                    ):
                        selected_detail = detail
                        selected_variant = variant
                        break

                if selected_variant is not None:
                    break

            if selected_variant is None:
                raise CommandError(
                    "No usable CJ variant found."
                )

            # -----------------------------
            # Prix de la variante
            # -----------------------------

            variant_price_usd = Decimal(
                str(
                    selected_variant[
                        "variantSellPrice"
                    ]
                )
            )

            # -----------------------------
            # Stock réel
            # -----------------------------

            variant_id = selected_variant["vid"]

            stock = cj_client.get_variant_stock(
                variant_id=variant_id,
            )

            # -----------------------------
            # Taux USD -> EUR réel
            # -----------------------------

            exchange_rate = exchange_rate_client.get_rate(
                from_currency="USD",
                to_currency="EUR",
            )

            # -----------------------------
            # Conversion
            # -----------------------------

            converted_price_eur = (
                conversion_service.convert(
                    amount=variant_price_usd,
                    from_currency="USD",
                    to_currency="EUR",
                    exchange_rate=exchange_rate,
                )
            )

        # -----------------------------
        # Affichage
        # -----------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "CJ real conversion test successful."
            )
        )

        self.stdout.write(
            "Product: "
            f"{selected_detail.get('productNameEn')}"
        )

        self.stdout.write(
            "Variant: "
            f"{selected_variant.get('variantNameEn')}"
        )

        self.stdout.write(
            f"Variant price USD: {variant_price_usd}"
        )

        self.stdout.write(
            f"USD -> EUR rate: {exchange_rate}"
        )

        self.stdout.write(
            "Converted supplier price EUR: "
            f"{converted_price_eur}"
        )

        self.stdout.write(
            f"Stock: {stock}"
        )

        