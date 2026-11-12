class PrintfulSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        matching_service,
        max_offers=5,
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
        return self._search(
            keyword=market_observation.name,
            market_observation=(
                market_observation
            ),
        )

    def search_for_idea(
        self,
        product_idea,
    ):
        supplier_keywords = (
            product_idea
            .supplier_search_keywords
            or []
        )

        keyword = (
            supplier_keywords[0]
            if supplier_keywords
            else product_idea.name
        )

        return self._search(
            keyword=keyword,
            product_idea=product_idea,
        )

    def _search(
        self,
        keyword,
        market_observation=None,
        product_idea=None,
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
                    second_name=keyword,
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

                offer_context = {
                    "supplier_search_keyword": keyword,
                }

                if market_observation is not None:
                    offer_context[
                        "market_observation"
                    ] = market_observation

                if product_idea is not None:
                    offer_context[
                        "product_idea"
                    ] = product_idea

                offer = (
                    self.offer_service
                    .create_offer_from_variant(
                        supplier=self.supplier,
                        product=product,
                        variant=variant,
                        **offer_context,
                    )
                )

                offers.append(
                    offer
                )

        return offers