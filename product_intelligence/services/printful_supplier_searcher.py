class PrintfulSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        matching_service,
        max_offers=10,
    ):
        self.client = client
        self.supplier = supplier
        self.offer_service = (
            offer_service
        )
        self.matching_service = (
            matching_service
        )
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

        products = (
            self.client.get_products()
        )

        for product_summary in products:
            if len(offers) >= self.max_offers:
                break

            product_id = product_summary.get(
                "id"
            )
            product_title = (
                product_summary.get("title")
                or ""
            )

            if not product_id:
                continue

            is_comparable = (
                self.matching_service
                .are_products_comparable(
                    first_name=product_title,
                    second_name=(
                        market_observation.name
                    ),
                )
            )

            if not is_comparable:
                continue

            result = self.client.get_product(
                product_id=product_id,
            )

            product = result.get(
                "product",
                {},
            )
            variants = result.get(
                "variants",
                [],
            )

            for variant in variants:
                if len(offers) >= self.max_offers:
                    break

                if not variant.get("id"):
                    continue

                offer = (
                    self.offer_service
                    .create_offer_from_variant(
                        supplier=self.supplier,
                        product=product,
                        variant=variant,
                        market_observation=(
                            market_observation
                        ),
                    )
                )

                offers.append(
                    offer
                )

        return offers
