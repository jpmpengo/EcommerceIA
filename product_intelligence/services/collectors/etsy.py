from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)


class EtsyMarketCollector(
    BaseMarketCollector
):

    source_name = "etsy"
    API_PAGE_SIZE = 25

    def __init__(
        self,
        client,
    ):
        self.client = client

    def collect(
        self,
        query,
    ):
        response = (
            self.client
            .search_active_listings(
                keywords=query,
                limit=self.API_PAGE_SIZE,
                offset=0,
            )
        )

        results = []

        for listing in response.get(
            "results",
            [],
        ):
            normalized = (
                self.client
                .normalize_listing(
                    listing
                )
            )

            results.append(
                {
                    "source": self.source_name,
                    "external_id": (
                        normalized[
                            "external_id"
                        ]
                    ),
                    "name": normalized[
                        "name"
                    ],
                    "description": (
                        listing.get(
                            "description",
                            "",
                        )
                    ),
                    "observed_price": (
                        normalized.get(
                            "observed_price"
                        )
                    ),
                    "currency": (
                        normalized.get(
                            "currency"
                        )
                        or "EUR"
                    ),
                    "product_url": (
                        normalized.get(
                            "product_url",
                            "",
                        )
                    ),
                    "image_url": (
                        self._get_image_url(
                            listing
                        )
                    ),
                    "raw_data": {
                        "query": query,
                        "listing": listing,
                    },
                }
            )

        return results

    @staticmethod
    def _get_image_url(
        listing,
    ):
        images = listing.get(
            "images",
            [],
        )

        if not images:
            return ""

        first_image = images[0]

        return (
            first_image.get(
                "url_fullxfull"
            )
            or first_image.get(
                "url_570xN"
            )
            or ""
        )