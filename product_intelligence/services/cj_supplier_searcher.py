class CJSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        max_offers=5,
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
        return self._search(
            keyword=product_idea.name,
            product_idea=product_idea,
        )

    def _search(
        self,
        keyword,
        market_observation=None,
        product_idea=None,
    ):
        offers = []

        products = self.client.search_products(
            keyword=keyword,
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

                offer_context = {}

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
                        stock=stock,
                        **offer_context,
                    )
                )

                offers.append(
                    offer
                )

        return offers
