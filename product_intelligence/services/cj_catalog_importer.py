from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)

from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)


class CJCatalogImporter:

    def __init__(
        self,
        client,
        supplier,
        keyword,
        max_offers=10,
        offer_service=None,
    ):
        self.client = client
        self.supplier = supplier
        self.keyword = keyword
        self.max_offers = max_offers

        self.offer_service = (
            offer_service
            or CJSupplierOfferService(
                variant_features_service=(
                    VariantFeaturesService()
                )
            )
        )

    def import_offers(
        self,
    ):
        offers = []

        products = self.client.search_products(
            keyword=self.keyword,
        )

        for product_data in products:
            if len(offers) >= self.max_offers:
                break

            product_id = (
                product_data.get("id")
                or product_data.get("pid")
            )

            if not product_id:
                continue

            product_detail = (
                self.client.get_product_detail(
                    product_id=product_id,
                )
            )

            product = (
                self.client.normalize_product(
                    product_detail,
                )
            )

            variants = (
                self.client.get_product_variants(
                    product_id=product_id,
                )
            )

            for variant in variants:
                if len(offers) >= self.max_offers:
                    break

                variant_id = variant.get(
                    "vid"
                )

                if not variant_id:
                    continue

                stock = (
                    self.client.get_variant_stock(
                        variant_id=variant_id,
                    )
                )

                offer = (
                    self.offer_service
                    .create_offer_from_variant(
                        supplier=self.supplier,
                        product=product,
                        variant=variant,
                        stock=stock,
                    )
                )

                offers.append(
                    offer
                )

        return offers

        