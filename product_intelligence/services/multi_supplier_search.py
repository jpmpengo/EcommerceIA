class MultiSupplierSearchService:

    MAX_OFFERS_PER_SUPPLIER = 5

    def __init__(
        self,
        supplier_searchers,
    ):
        self.supplier_searchers = (
            supplier_searchers
        )

    def search(
        self,
        market_observation,
    ):
        offers = []

        for searcher in self.supplier_searchers:
            can_handle = getattr(
                searcher,
                "can_handle",
                None,
            )

            if can_handle is not None:
                if not can_handle(
                    market_observation
                ):
                    continue

            supplier_offers = (
                searcher.search_offers(
                    market_observation=(
                        market_observation
                    ),
                )
            )

            offers.extend(
                supplier_offers
            )

        return offers

    def search_for_idea(
        self,
        product_idea,
    ):
        offers = []

        for searcher in self.supplier_searchers:
            supplier_offers = (
                searcher.search_for_idea(
                    product_idea=product_idea,
                )
            )

            offers.extend(
                supplier_offers[
                    :self.MAX_OFFERS_PER_SUPPLIER
                ]
            )

        return offers