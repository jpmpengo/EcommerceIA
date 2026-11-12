class EproloSupplierSearcher:

    def __init__(
        self,
        client,
        supplier,
        offer_service,
        matching_service,
        category_resolver,
        max_offers=5,
        max_catalog_pages=5,
    ):
        self.client = client
        self.supplier = supplier
        self.offer_service = offer_service
        self.matching_service = matching_service
        self.category_resolver = category_resolver
        self.max_offers = max_offers
        self.max_catalog_pages = max_catalog_pages

    def can_handle(self, market_observation):
        return bool(
            market_observation
            and market_observation.name
        )

    def search_offers(self, market_observation):
        return self._search(
            keyword=market_observation.name,
            market_observation=market_observation,
        )

    def search_for_idea(self, product_idea):
        keywords = list(
            product_idea.supplier_search_keywords
            or [product_idea.name]
        )
        offers = []
        seen_products = set()
        category = self.category_resolver.resolve(
            product_idea.name,
            " ".join(keywords),
        )
        if category is None:
            return []
        for keyword in keywords:
            if len(offers) >= self.max_offers:
                break
            products = self.client.search_products(
                keyword=keyword,
                matching_service=self.matching_service,
                **category,
                max_pages=self.max_catalog_pages,
                max_results=self.max_offers,
            )
            offers.extend(
                self._offers_from_products(
                    products,
                    product_idea=product_idea,
                    seen_products=seen_products,
                    supplier_search_keyword=keyword,
                )
            )
        return offers[:self.max_offers]

    def _search(
        self,
        keyword,
        market_observation=None,
    ):
        category = self.category_resolver.resolve(keyword)
        if category is None:
            return []
        products = self.client.search_products(
            keyword=keyword,
            matching_service=self.matching_service,
            **category,
            max_pages=self.max_catalog_pages,
            max_results=self.max_offers,
        )
        return self._offers_from_products(
            products,
            market_observation=market_observation,
        )[:self.max_offers]

    def _offers_from_products(
        self,
        products,
        market_observation=None,
        product_idea=None,
        seen_products=None,
        supplier_search_keyword=None,
    ):
        offers = []
        if seen_products is None:
            seen_products = set()
        for product in products:
            product_id = product.get("id")
            if not product_id or product_id in seen_products:
                continue
            variants = product.get("variantlist") or []
            for variant in variants:
                if (
                    not isinstance(variant, dict)
                    or not variant.get("id")
                    or variant.get("cost") is None
                ):
                    continue
                offer = self.offer_service.create_offer_from_variant(
                    supplier=self.supplier,
                    product=product,
                    variant=variant,
                    market_observation=market_observation,
                    product_idea=product_idea,
                    supplier_search_keyword=(
                        supplier_search_keyword or ""
                    ),
                )
                offers.append(offer)
                seen_products.add(product_id)
                break
            if len(offers) >= self.max_offers:
                break
        return offers
