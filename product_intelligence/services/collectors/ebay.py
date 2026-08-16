from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)


class EbayCollector(BaseMarketCollector):
    source_name = "ebay"

    def __init__(self, client):
        self.client = client

    def collect(self, query):
        response = self.client.search(
            query=query
        )

        results = []

        for item in response.get(
            "itemSummaries",
            [],
        ):
            price = item.get(
                "price",
                {},
            )

            image = item.get(
                "image",
                {},
            )

            results.append(
                {
                    "source": self.source_name,
                    "external_id": item.get(
                        "itemId",
                        "",
                    ),
                    "name": item.get(
                        "title",
                        "",
                    ),
                    "description": "",
                    "observed_price": price.get(
                        "value",
                    ),
                    "currency": price.get(
                        "currency",
                        "EUR",
                    ),
                    "product_url": item.get(
                        "itemWebUrl",
                        "",
                    ),
                    "image_url": image.get(
                        "imageUrl",
                        "",
                    ),
                    "raw_data": item,
                }
            )

        return results

        