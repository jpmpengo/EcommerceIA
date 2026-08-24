from unittest import TestCase
from unittest.mock import Mock

from product_intelligence.services.collectors.etsy import (
    EtsyMarketCollector,
)


class EtsyMarketCollectorTests(TestCase):

    def test_collect_returns_normalized_observations(
        self,
    ):
        client = Mock()

        raw_listing = {
            "listing_id": 987654321,
            "title": "Under sink organizer",
            "price": {
                "amount": 2490,
                "divisor": 100,
                "currency_code": "EUR",
            },
            "url": (
                "https://www.etsy.com/"
                "listing/987654321"
            ),
        }

        client.search_active_listings.return_value = {
            "count": 1,
            "results": [
                raw_listing,
            ],
        }

        client.normalize_listing.return_value = {
            "external_id": "987654321",
            "name": "Under sink organizer",
            "observed_price": "24.90",
            "currency": "EUR",
            "product_url": (
                "https://www.etsy.com/"
                "listing/987654321"
            ),
        }

        collector = EtsyMarketCollector(
            client=client
        )

        results = collector.collect(
            query="organisateur sous évier"
        )

        client.search_active_listings.assert_called_once_with(
            keywords="organisateur sous évier",
            limit=25,
            offset=0,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["source"],
            "etsy",
        )

        self.assertEqual(
            results[0]["external_id"],
            "987654321",
        )

        self.assertEqual(
            results[0]["raw_data"][
                "query"
            ],
            "organisateur sous évier",
        )

        self.assertEqual(
            results[0]["raw_data"][
                "listing"
            ],
            raw_listing,
        )