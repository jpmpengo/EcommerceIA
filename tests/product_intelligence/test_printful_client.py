from django.test import SimpleTestCase

from product_intelligence.services.printful_client import (
    PrintfulClient,
)


class PrintfulClientTests(SimpleTestCase):

    def test_get_products_returns_catalog_products(
        self,
    ):
        class FakeResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": [
                        {
                            "id": 938,
                            "title": "Luggage Tag",
                            "currency": "USD",
                            "variant_count": 1,
                        },
                        {
                            "id": 924,
                            "title": "Area Rug",
                            "currency": "USD",
                            "variant_count": 6,
                        },
                    ],
                }

        class FakeHTTPClient:
            def get(
                self,
                url,
                headers=None,
            ):
                return FakeResponse()

        client = PrintfulClient(
            api_token="test-token",
            http_client=FakeHTTPClient(),
        )

        products = client.get_products()

        self.assertEqual(
            len(products),
            2,
        )

        self.assertEqual(
            products[0]["id"],
            938,
        )

        self.assertEqual(
            products[0]["title"],
            "Luggage Tag",
        )

    def test_get_products_sends_expected_request(
        self,
    ):
        calls = []

        class FakeResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": [],
                }

        class FakeHTTPClient:
            def get(
                self,
                url,
                headers=None,
            ):
                calls.append(
                    {
                        "url": url,
                        "headers": headers,
                    }
                )
                return FakeResponse()

        client = PrintfulClient(
            api_token="test-token",
            http_client=FakeHTTPClient(),
        )

        client.get_products()

        self.assertEqual(
            len(calls),
            1,
        )

        self.assertEqual(
            calls[0]["url"],
            "https://api.printful.com/products",
        )

        self.assertEqual(
            calls[0]["headers"],
            {
                "Authorization": "Bearer test-token",
            },
        )

    def test_get_product_returns_product_detail(
        self,
    ):
        class FakeResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": {
                        "product": {
                            "id": 583,
                            "title": "Gaming Mouse Pad",
                            "currency": "USD",
                        },
                        "variants": [
                            {
                                "id": 15662,
                                "product_id": 583,
                                "name": "Gaming Mouse Pad - 18 x 16",
                            },
                            {
                                "id": 15663,
                                "product_id": 583,
                                "name": "Gaming Mouse Pad - 36 x 18",
                            },
                        ],
                    },
                }

        class FakeHTTPClient:
            def get(
                self,
                url,
                headers=None,
            ):
                return FakeResponse()

        client = PrintfulClient(
            api_token="test-token",
            http_client=FakeHTTPClient(),
        )

        product = client.get_product(
            product_id=583,
        )

        self.assertEqual(
            product["product"]["id"],
            583,
        )

        self.assertEqual(
            product["product"]["title"],
            "Gaming Mouse Pad",
        )

        self.assertEqual(
            len(product["variants"]),
            2,
        )

    def test_get_product_exposes_variant_offer_data(
        self,
    ):
        class FakeResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": {
                        "product": {
                            "id": 583,
                            "title": "Gaming Mouse Pad",
                            "currency": "USD",
                        },
                        "variants": [
                            {   
                                "id": 14943,
                                "product_id": 583,
                                "name": (
                                    "Gaming Mouse Pad "
                                    '(White / 18"x16")'
                                ),
                                "price": "11.72",
                            },
                        ],
                    },
                }

        class FakeHTTPClient:
            def get(
                self,
                url,
                headers=None,
            ):
                return FakeResponse()

        client = PrintfulClient(
            api_token="test-token",
            http_client=FakeHTTPClient(),
        )

        result = client.get_product(
            product_id=583,
        )

        product = result["product"]
        variant = result["variants"][0]

        self.assertEqual(
            product["id"],
            583,
        )
        self.assertEqual(
            product["currency"],
            "USD",
        )
        self.assertEqual(
            variant["id"],
            14943,
        )
        self.assertEqual(
            variant["product_id"],
            583,
        )
        self.assertEqual(
            variant["price"],
            "11.72",
        )