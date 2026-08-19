class CJSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        max_offers=10,
    ):
        self.client = client
        self.supplier = supplier
        self.offer_service = offer_service
        self.max_offers = max_offers

    def can_handle(
        self,
        market_observation,
    ):
        return bool(
            market_observation
            and market_observation.name
        )

    def search_offers(
        self,
        market_observation,
    ):
        offers = []

        products = self.client.search_products(
            keyword=market_observation.name,
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

            if not product_detail:
                continue

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

                variant_id = variant.get("vid")

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
                        market_observation=(
                            market_observation
                        ),
                    )
                )

                offers.append(offer)

        return offers
