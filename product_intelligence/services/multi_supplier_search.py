import httpx

class MultiSupplierSearchService:

    MAX_OFFERS_PER_SUPPLIER = 5

    def __init__(
        self,
        supplier_searchers,
    ):
        self.supplier_searchers = (
            supplier_searchers
        )
        self.supplier_failures = {}

    def search(
        self,
        market_observation,
    ):
        offers = []
        self.supplier_failures = {}

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

            try:
                supplier_offers = (
                    searcher.search_offers(
                        market_observation=(
                            market_observation
                        ),
                    )
                )
            except httpx.HTTPError as exc:
                supplier_name = (
                    getattr(
                        getattr(searcher, "supplier", None),
                        "name",
                        searcher.__class__.__name__,
                    )
                )
                if isinstance(exc, httpx.HTTPStatusError):
                    reason = f"HTTP {exc.response.status_code}"
                else:
                    reason = exc.__class__.__name__
                self.supplier_failures[supplier_name] = reason
                continue

            offers.extend(
                supplier_offers
            )

        return offers

    def search_for_idea(
        self,
        product_idea,
    ):
        offers = []
        self.supplier_failures = {}

        for searcher in self.supplier_searchers:
            try:
                supplier_offers = (
                    searcher.search_for_idea(
                        product_idea=product_idea,
                    )
                )
            except httpx.HTTPError as exc:
                supplier_name = (
                    getattr(
                        getattr(searcher, "supplier", None),
                        "name",
                        searcher.__class__.__name__,
                    )
                )
                if isinstance(exc, httpx.HTTPStatusError):
                    reason = f"HTTP {exc.response.status_code}"
                else:
                    reason = exc.__class__.__name__
                self.supplier_failures[supplier_name] = reason
                continue

            offers.extend(
                supplier_offers[
                    :self.MAX_OFFERS_PER_SUPPLIER
                ]
            )

        return offers