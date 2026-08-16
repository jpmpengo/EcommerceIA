import os
import ssl
from decimal import Decimal

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
from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)


class Command(BaseCommand):
    help = (
        "Teste le pipeline réel CJ jusqu'à SupplierOffer "
        "et ProductOpportunity."
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

            # --------------------------------
            # 1. Authentification CJ
            # --------------------------------

            auth_client = CJAuthClient(
                api_key=api_key,
                http_client=http_client,
            )

            access_token = auth_client.get_access_token()

            cj_client = CJClient(
                access_token=access_token,
                http_client=http_client,
            )

            # --------------------------------
            # 2. Services de conversion
            # --------------------------------

            exchange_rate_client = ExchangeRateClient(
                http_client=http_client,
            )

            conversion_service = CurrencyConversionService()

            # --------------------------------
            # 3. Recherche produit CJ
            # --------------------------------

            products = cj_client.search_products(
                keyword="wireless charger",
            )

            if not products:
                raise CommandError(
                    "CJ returned no products."
                )

            selected_detail = None
            selected_variant = None

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
                    variant_id = variant.get("vid")
                    variant_price = variant.get(
                        "variantSellPrice"
                    )

                    if (
                        variant_id
                        and variant_price is not None
                    ):
                        selected_detail = detail
                        selected_variant = variant
                        break

                if selected_variant is not None:
                    break

            if selected_detail is None:
                raise CommandError(
                    "No usable CJ product found."
                )

            if selected_variant is None:
                raise CommandError(
                    "No usable CJ variant found."
                )

            # --------------------------------
            # 4. Données CJ
            # --------------------------------

            product_name = (
                selected_detail.get("productNameEn")
                or "CJ Product"
            )

            product_id = (
                selected_detail.get("pid")
                or selected_detail.get("id")
            )

            variant_id = selected_variant["vid"]

            variant_price_usd = Decimal(
                str(
                    selected_variant[
                        "variantSellPrice"
                    ]
                )
            )

            # --------------------------------
            # 5. Vérification du taux réel
            # --------------------------------
            #
            # On peut récupérer le taux ici pour
            # l'afficher.
            #
            # Contrairement au stock, cela ne
            # modifie pas les données fournisseur.

            exchange_rate = exchange_rate_client.get_rate(
                from_currency="USD",
                to_currency="EUR",
            )

            converted_price = conversion_service.convert(
                amount=variant_price_usd,
                from_currency="USD",
                to_currency="EUR",
                exchange_rate=exchange_rate,
            )

            self.stdout.write("")

            self.stdout.write(
                self.style.SUCCESS(
                    "Real CJ data retrieved successfully."
                )
            )

            self.stdout.write(
                f"Product: {product_name}"
            )

            self.stdout.write(
                f"CJ product ID: {product_id}"
            )

            self.stdout.write(
                "Variant: "
                f"{selected_variant.get('variantNameEn')}"
            )

            self.stdout.write(
                f"Variant ID: {variant_id}"
            )

            self.stdout.write(
                f"Variant price USD: {variant_price_usd}"
            )

            self.stdout.write(
                f"USD -> EUR rate: {exchange_rate}"
            )

            self.stdout.write(
                "Preview converted price EUR: "
                f"{converted_price}"
            )

            # --------------------------------
            # 6. Supplier
            # --------------------------------

            supplier, _ = Supplier.objects.get_or_create(
                name="CJdropshipping",
                defaults={
                    "country": "CN",
                    "website": "https://cjdropshipping.com",
                    "supplier_type": "dropshipper",
                },
            )

            # --------------------------------
            # 7. Observation marché contrôlée
            # --------------------------------

            observation, _ = (
                MarketObservation.objects.update_or_create(
                    source="manual-cj-test",
                    external_id=f"CJ-REAL-{variant_id}",
                    defaults={
                        "name": product_name,
                        "observed_price": Decimal("19.90"),
                        "currency": "EUR",
                        "product_url": "",
                        "raw_data": {
                            "cj_product_id": str(product_id),
                            "cj_variant_id": str(variant_id),
                        },
                    },
                )
            )

            # --------------------------------
            # 8. Produit normalisé
            # --------------------------------

            normalized_product = {
                "external_id": str(product_id),
                "name": product_name,
                "currency": "USD",
                "product_url": "",
            }

            # --------------------------------
            # 9. Pipeline
            # --------------------------------
            #
            # IMPORTANT :
            # C'est maintenant le SEUL endroit
            # où get_variant_stock() est appelé.

            pipeline = CJPipelineService(
                client=cj_client,
                offer_service=CJSupplierOfferService(),
                opportunity_service=(
                    SupplierOfferOpportunityService()
                ),
                currency_conversion_service=(
                    conversion_service
                ),
                exchange_rate_client=(
                    exchange_rate_client
                ),
            )

            opportunity = (
                pipeline.build_opportunity_from_variant(
                    supplier=supplier,
                    product=normalized_product,
                    variant=selected_variant,
                    market_observation=observation,
                )
            )

            # --------------------------------
            # 10. Offre réellement liée
            # à cette observation
            # --------------------------------

            offer = supplier.offers.filter(
                market_observation=observation,
            ).order_by(
                "-observed_at"
            ).first()

        # --------------------------------
        # Plus aucun appel HTTP après ici.
        # --------------------------------

        if offer is None:
            raise CommandError(
                "SupplierOffer was not created."
            )

        if opportunity is None:
            raise CommandError(
                "ProductOpportunity was not created."
            )

        # --------------------------------
        # 11. Résultat enregistré
        # --------------------------------

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Real CJ pipeline completed successfully."
            )
        )

        self.stdout.write(
            f"SupplierOffer ID: {offer.id}"
        )

        self.stdout.write(
            "SupplierOffer price: "
            f"{offer.purchase_price} "
            f"{offer.currency}"
        )

        self.stdout.write(
            f"SupplierOffer stock: {offer.stock}"
        )

        self.stdout.write(
            f"MarketObservation ID: {observation.id}"
        )

        self.stdout.write(
            f"ProductOpportunity ID: {opportunity.id}"
        )

        self.stdout.write(
            "Opportunity supplier price: "
            f"{opportunity.supplier_price}"
        )

        self.stdout.write(
            "Opportunity market price: "
            f"{opportunity.market_price}"
        )

        self.stdout.write(
            "Opportunity total cost: "
            f"{opportunity.get_total_cost()}"
        )

        self.stdout.write(
            "Opportunity margin: "
            f"{opportunity.get_estimated_margin()}"
        )

        self.stdout.write(
            "Opportunity score: "
            f"{opportunity.opportunity_score}"
        )
        

