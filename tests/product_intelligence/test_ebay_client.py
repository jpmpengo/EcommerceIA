from django.test import SimpleTestCase

from product_intelligence.services.ebay_client import (
    EbayClient,
)


class FakeResponse:

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeHttpClient:

    def __init__(self):
        self.last_url = None
        self.last_params = None
        self.last_headers = None

    def get(
        self,
        url,
        params=None,
        headers=None,
    ):
        self.last_url = url
        self.last_params = params
        self.last_headers = headers

        return FakeResponse(
            {
                "itemSummaries": [
                    {
                        "itemId": "EBAY123",
                        "title": (
                            "Support ordinateur portable"
                        ),
                    }
                ]
            }
        )


class EbayClientTests(SimpleTestCase):

    def test_search_calls_ebay_browse_api(self):
        http_client = FakeHttpClient()

        client = EbayClient(
            access_token="fake-token",
            http_client=http_client,
        )

        result = client.search(
            query="support ordinateur portable"
        )

        self.assertEqual(
            http_client.last_url,
            (
                "https://api.ebay.com/"
                "buy/browse/v1/item_summary/search"
            ),
        )

        self.assertEqual(
            http_client.last_params["q"],
            "support ordinateur portable",
        )

        self.assertEqual(
            http_client.last_headers["Authorization"],
            "Bearer fake-token",
        )

        self.assertEqual(
            result["itemSummaries"][0]["itemId"],
            "EBAY123",
        )

    def test_search_sends_marketplace_id(self):
        http_client = FakeHttpClient()

        client = EbayClient(
            access_token="fake-token",
            http_client=http_client,
            marketplace_id="EBAY_FR",
        )

        client.search(
            query="support ordinateur portable"
        )

        self.assertEqual(
            http_client.last_headers[
                "X-EBAY-C-MARKETPLACE-ID"
            ],
            "EBAY_FR",
        )

        
