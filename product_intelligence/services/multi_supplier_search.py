class MultiSupplierSearchService:

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
