from product_intelligence.services.printful_supplier_offer import (
    PrintfulSupplierOfferService,
)

from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)


class PrintfulCatalogImporter:

    def __init__(
        self,
        client,
        supplier,
        max_offers=10,
        offer_service=None,
    ):
        self.client = client
        self.supplier = supplier
        self.max_offers = max_offers

        self.offer_service = (
            offer_service
            or PrintfulSupplierOfferService(
                variant_features_service=(
                    VariantFeaturesService()
                )
            )
        )

    def import_offers(
        self,
    ):
        offers = []

        products = self.client.get_products()

        for product_data in products:
            if len(offers) >= self.max_offers:
                break

            product_id = product_data.get(
                "id"
            )

            if product_id is None:
                continue

            result = self.client.get_product(
                product_id=product_id,
            )

            product = result.get(
                "product"
            )

            variants = result.get(
                "variants",
                [],
            )

            if not isinstance(product, dict):
                continue

            if not isinstance(variants, list):
                continue

            for variant in variants:
                if len(offers) >= self.max_offers:
                    break

                if not isinstance(
                    variant,
                    dict,
                ):
                    continue

                if variant.get("id") is None:
                    continue

                offer = (
                    self.offer_service
                    .create_offer_from_variant(
                        supplier=self.supplier,
                        product=product,
                        variant=variant,
                    )
                )

                offers.append(
                    offer
                )

        return offers

        