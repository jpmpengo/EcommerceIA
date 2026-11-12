class CJSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        max_offers=5,
        category_matching_service=None,
        sleep_func=None,
        request_delay=1.3,
    ):
        self.client = client
        self.supplier = supplier
        self.offer_service = offer_service
        self.max_offers = max_offers
        self.category_matching_service = (
            category_matching_service
        )
        self.sleep_func = sleep_func
        self.request_delay = request_delay

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
        search_count = 0

        localized = getattr(
            product_idea,
            "supplier_search_keywords_localized",
            {},
        )
        if not isinstance(localized, dict):
            localized = {}

        def search_country(country_code):
            nonlocal search_count
            localized_by_country = localized.get(country_code, {})
            for keyword in supplier_keywords:
                remaining_offers = (
                    self.max_offers
                    - len(offers)
                )

                if remaining_offers <= 0:
                    break

                if (
                    search_count > 0
                    and self.sleep_func is not None
                    and self.request_delay > 0
                ):
                    self.sleep_func(
                        self.request_delay
                    )

                localized_keyword = localized_by_country.get(keyword)
                alternative_keywords = (
                    [localized_keyword]
                    if localized_keyword
                    else []
                )

                keyword_offers = self._search(
                    keyword=keyword,
                    product_idea=product_idea,
                    max_offers=remaining_offers,
                    seen_product_ids=(
                        seen_product_ids
                    ),
                    country_code=country_code,
                    alternative_keywords=alternative_keywords,
                )

                search_count += 1

                offers.extend(
                    keyword_offers
                )

        search_country("CN")


        return offers

    def search_for_idea_in_country(
        self,
        product_idea,
        country_code,
    ):
        supplier_keywords = list(
            product_idea.supplier_search_keywords
            or []
        )

        if not supplier_keywords:
            supplier_keywords = [
                product_idea.name,
            ]

        offers = []
        seen_product_ids = set()
        search_count = 0

        for keyword in supplier_keywords:
            remaining_offers = (
                self.max_offers
                - len(offers)
            )

            if remaining_offers <= 0:
                break

            if (
                search_count > 0
                and self.sleep_func is not None
                and self.request_delay > 0
            ):
                self.sleep_func(
                    self.request_delay
                )

            keyword_offers = self._search(
                keyword=keyword,
                product_idea=product_idea,
                max_offers=remaining_offers,
                seen_product_ids=seen_product_ids,
                country_code=country_code,
            )

            search_count += 1
            offers.extend(keyword_offers)

        return offers

    def _search(
        self,
        keyword,
        market_observation=None,
        product_idea=None,
        max_offers=None,
        seen_product_ids=None,
        country_code=None,
        alternative_keywords=None,
    ):
        offers = []

        offer_limit = (
            max_offers
            if max_offers is not None
            else self.max_offers
        )

        if seen_product_ids is None:
            seen_product_ids = set()

        search_kwargs = {
            "keyword": keyword,
        }

        if country_code:
            search_kwargs["country_code"] = (
                country_code
            )

        products = self.client.search_products(
            **search_kwargs
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
                        alternative_keywords=(
                            alternative_keywords or []
                        ),
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

                stock_kwargs = {
                    "variant_id": variant_id,
                }

                if country_code:
                    stock_kwargs["country_code"] = (
                        country_code
                    )

                stock = (
                    self.client.get_variant_stock(
                        **stock_kwargs
                    )
                )

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

                if country_code:
                    offer_context[
                        "stock_country"
                    ] = country_code

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