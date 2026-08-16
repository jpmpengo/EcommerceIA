import os
import ssl

import httpx
import truststore

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient


class Command(BaseCommand):
    help = "Teste un produit CJ multivariante et son stock réel."

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
            # Authentification
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
            # Recherche produit
            # -----------------------------

            products = cj_client.search_products(
                keyword="wireless charger",
            )

            if not products:
                raise CommandError(
                    "CJ returned no products."
                )

            selected_detail = None
            selected_product_id = None

            # -----------------------------
            # Trouver un produit ayant
            # plusieurs variantes
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

                normalized = cj_client.normalize_product(detail)

                self.stdout.write("")
                self.stdout.write("=== NORMALIZED PRODUCT ===")
                self.stdout.write(
                    f"External ID: {normalized.get('external_id')}"
                )
                self.stdout.write(
                    f"Name: {normalized.get('name')}"
                )
                self.stdout.write(
                    f"Purchase price: {normalized.get('purchase_price')}"
                )
                self.stdout.write(
                    f"Purchase price type: "
                    f"{type(normalized.get('purchase_price')).__name__}"
                )
                self.stdout.write(
                    f"Currency: {normalized.get('currency')!r}"
                )
                self.stdout.write("==========================")

                variants = detail.get("variants") or []

                if len(variants) > 1:
                    selected_detail = detail
                    selected_product_id = product_id
                    break

            if selected_detail is None:
                self.stdout.write(
                    self.style.WARNING(
                        "No multi-variant product found."
                    )
                )
                return

            # -----------------------------
            # Première variante
            # -----------------------------

            variants = selected_detail.get("variants") or []

            first_variant = variants[0]

            variant_id = first_variant.get("vid")

            if not variant_id:
                raise CommandError(
                    "CJ variant has no vid."
                )

            # -----------------------------
            # Appel réel du stock CJ
            # -----------------------------

            stock = cj_client.get_variant_stock(
                variant_id=variant_id,
            )

        # -----------------------------
        # Résultats
        # -----------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "CJ multi-variant product found."
            )
        )

        self.stdout.write(
            f"Product ID: {selected_product_id}"
        )

        self.stdout.write(
            "Product name: "
            f"{selected_detail.get('productNameEn')}"
        )

        self.stdout.write(
            "Product sell price: "
            f"{selected_detail.get('sellPrice')}"
        )

        self.stdout.write(
            "Product currency: "
            f"{selected_detail.get('currency')}"
        )

        self.stdout.write(
            f"Variant count: {len(variants)}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "First variant:"
            )
        )

        self.stdout.write(
            f"Variant ID: {variant_id}"
        )

        self.stdout.write(
            "Variant SKU: "
            f"{first_variant.get('variantSku')}"
        )

        self.stdout.write(
            "Variant name: "
            f"{first_variant.get('variantNameEn')}"
        )

        self.stdout.write(
            "Variant sell price: "
            f"{first_variant.get('variantSellPrice')}"
        )

        self.stdout.write(
            "Variant weight: "
            f"{first_variant.get('variantWeight')}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "CJ stock request successful."
            )
        )

        self.stdout.write(
            f"Variant stock: {stock}"
        )

        



        