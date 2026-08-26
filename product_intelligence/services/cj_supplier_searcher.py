class CJSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        max_offers=5,
        category_matching_service=None,
    ):
        self.client = client
        self.supplier = supplier
        self.offer_service = offer_service
        self.max_offers = max_offers
        self.category_matching_service = (
            category_matching_service
        )

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
        supplier_keywords = list(
            product_idea
            .supplier_search_keywords
            or []
        )

        if not supplier_keywords:
            supplier_keywords = [
                product_idea.name,
            ]

        offers = []
        seen_product_ids = set()

        for keyword in supplier_keywords:
            remaining_offers = (
                self.max_offers
                - len(offers)
            )

            if remaining_offers <= 0:
                break

            keyword_offers = self._search(
                keyword=keyword,
                product_idea=product_idea,
                max_offers=remaining_offers,
                seen_product_ids=(
                    seen_product_ids
                ),
            )

            offers.extend(
                keyword_offers
            )

        return offers

    def _search(
        self,
        keyword,
        market_observation=None,
        product_idea=None,
        max_offers=None,
        seen_product_ids=None,
    ):
        offers = []

        offer_limit = (
            max_offers
            if max_offers is not None
            else self.max_offers
        )

        if seen_product_ids is None:
            seen_product_ids = set()

        products = self.client.search_products(
            keyword=keyword,
        )

        for product_data in products:
            if len(offers) >= offer_limit:
                break

            product_id = (
                product_data.get("id")
                or product_data.get("pid")
            )

            if (
                not product_id
                or product_id
                in seen_product_ids
            ):
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

            if (
                product_idea is not None
                and self.category_matching_service
                is not None
            ):
                is_relevant = (
                    self.category_matching_service
                    .is_relevant(
                        product_name=(
                            product["name"]
                        ),
                        search_keyword=keyword,
                    )
                )

                if not is_relevant:
                    continue

            variants = (
                self.client.get_product_variants(
                    product_id=product_id,
                )
            )

            for variant in variants:
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

                seen_product_ids.add(
                    product_id
                )

                break

        return offers