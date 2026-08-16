import httpx

from django.test import SimpleTestCase
from unittest.mock import Mock, patch

from product_intelligence.services.cj_client import (
    CJClient,
)


class CJClientTests(SimpleTestCase):

    # ============================================================
    # SEARCH PRODUCTS
    # ============================================================

    def test_search_products_sends_expected_request(self):
        class FakeResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": {
                        "content": [],
                    },
                }

        class FakeHTTPClient:
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

                return FakeResponse()

        http_client = FakeHTTPClient()

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        client.search_products(
            keyword="wireless charger",
        )

        self.assertEqual(
            http_client.last_params,
            {
                "page": 1,
                "size": 20,
                "keyWord": "wireless charger",
            },
        )

        self.assertEqual(
            http_client.last_headers[
                "CJ-Access-Token"
            ],
            "test-token",
        )

    def test_search_products_returns_product_content(
        self,
    ):
        class FakeResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": {
                        "content": [
                            {
                                "productList": [
                                    {
                                        "id": "CJ-123",
                                        "nameEn": (
                                            "Wireless Charger"
                                        ),
                                    }
                                ],
                                "relatedCategoryList": [],
                                "keyWord": (
                                    "wireless charger"
                                ),
                                "keyWordOld": None,
                            }
                        ],
                    },
                }

        class FakeHTTPClient:
            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                return FakeResponse()

        client = CJClient(
            access_token="test-token",
            http_client=FakeHTTPClient(),
        )

        products = client.search_products(
            keyword="wireless charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

    def test_search_products_extracts_product_list_v2(
        self,
    ):
        class ProductListV2Response:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": {
                        "content": [
                            {
                                "productList": [
                                    {
                                        "id": "CJ-123",
                                        "nameEn": (
                                            "Wireless Charger"
                                        ),
                                        "sellPrice": "8.75",
                                    },
                                    {
                                        "id": "CJ-456",
                                        "nameEn": (
                                            "USB Charger"
                                        ),
                                        "sellPrice": "6.50",
                                    },
                                ],
                                "relatedCategoryList": [],
                                "keyWord": (
                                    "wireless charger"
                                ),
                                "keyWordOld": None,
                            }
                        ]
                    },
                }

        class ProductListV2HTTPClient:
            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                return ProductListV2Response()

        client = CJClient(
            access_token="test-token",
            http_client=ProductListV2HTTPClient(),
        )

        products = client.search_products(
            keyword="wireless charger",
        )

        self.assertEqual(
            len(products),
            2,
        )

        self.assertEqual(
            products[0]["id"],
            "CJ-123",
        )

        self.assertEqual(
            products[1]["id"],
            "CJ-456",
        )

    def test_search_products_returns_empty_list_when_cj_data_is_none(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": False,
            "message": "Temporary error",
            "data": None,
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_data_key_is_missing(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": True,
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_content_is_none(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": None,
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_response_json_is_invalid(
        self,
    ):
        response = Mock()

        response.json.side_effect = ValueError(
            "Invalid JSON"
        )

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_on_timeout(
        self,
    ):
        http_client = Mock()

        http_client.get.side_effect = (
            httpx.TimeoutException(
                "CJ request timed out"
            )
        )

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_cj_result_is_false(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 500,
            "result": False,
            "message": "CJ internal error",
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_content_is_not_a_list(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": {
                    "productList": [
                        {
                            "id": "CJ-123",
                            "nameEn": (
                                "Wireless Charger"
                            ),
                        }
                    ],
                },
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_product_list_is_not_a_list(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": {
                            "id": "CJ-123",
                            "nameEn": (
                                "Wireless Charger"
                            ),
                        },
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    def test_search_products_returns_empty_list_when_first_content_item_is_not_a_dict(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    "unexpected-value",
                ],
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

    # ============================================================
    # RETRIES
    # ============================================================

    def test_search_products_retries_once_on_503_then_succeeds(
        self,
    ):
        first_response = Mock()
        first_response.status_code = 503

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    def test_search_products_retries_only_once_on_repeated_503(
        self,
    ):
        first_response = Mock()
        first_response.status_code = 503
        first_response.json.return_value = {
            "code": 503,
            "result": False,
            "data": None,
        }

        second_response = Mock()
        second_response.status_code = 503
        second_response.json.return_value = {
            "code": 503,
            "result": False,
            "data": None,
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [],
        )

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    def test_search_products_retries_once_on_429_then_succeeds(
        self,
    ):
        first_response = Mock()
        first_response.status_code = 429

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    def test_search_products_retries_once_on_500_then_succeeds(
        self,
    ):
        first_response = Mock()
        first_response.status_code = 500

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    def test_search_products_retries_once_on_502_then_succeeds(
        self,
    ):
        first_response = Mock()
        first_response.status_code = 502

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    @patch(
        "product_intelligence.services.cj_client.time.sleep"
    )
    def test_search_products_waits_retry_after_on_429_then_succeeds(
        self,
        mock_sleep,
    ):
        first_response = Mock()
        first_response.status_code = 429
        first_response.headers = {
            "Retry-After": "2",
        }

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

        mock_sleep.assert_called_once_with(
            2.0
        )

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    @patch(
        "product_intelligence.services.cj_client.time.sleep"
    )
    def test_search_products_ignores_invalid_retry_after_on_429(
        self,
        mock_sleep,
    ):
        first_response = Mock()
        first_response.status_code = 429
        first_response.headers = {
            "Retry-After": "soon",
        }

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "content": [
                    {
                        "productList": [
                            {
                                "id": "CJ-123",
                                "nameEn": (
                                    "Wireless Charger"
                                ),
                            }
                        ],
                    }
                ],
            },
        }

        http_client = Mock()
        http_client.get.side_effect = [
            first_response,
            second_response,
        ]

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        products = client.search_products(
            keyword="Wireless Charger",
        )

        self.assertEqual(
            products,
            [
                {
                    "id": "CJ-123",
                    "nameEn": "Wireless Charger",
                }
            ],
        )

        mock_sleep.assert_not_called()

        self.assertEqual(
            http_client.get.call_count,
            2,
        )

    # ============================================================
    # NORMALIZE PRODUCT
    # ============================================================

    def test_normalizes_product(self):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        product = {
            "pid": "CJ-123",
            "productNameEn": "Wireless Charger",
            "productImage": (
                "https://example.com/image.jpg"
            ),
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized,
            {
                "external_id": "CJ-123",
                "name": "Wireless Charger",
                "image_url": (
                    "https://example.com/image.jpg"
                ),
                "currency": "USD",
            },
        )

    def test_normalizes_product_with_supplier_price(
        self,
    ):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        product = {
            "pid": "CJ-123",
            "productNameEn": "Wireless Charger",
            "productImage": (
                "https://example.com/image.jpg"
            ),
            "sellPrice": "8.75",
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized,
            {
                "external_id": "CJ-123",
                "name": "Wireless Charger",
                "image_url": (
                    "https://example.com/image.jpg"
                ),
                "purchase_price": "8.75",
                "currency": "USD",
            },
        )

    def test_normalizes_product_list_v2_format(
        self,
    ):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        product = {
            "id": "CJ-123",
            "nameEn": "Wireless Charger",
            "bigImage": (
                "https://example.com/image.jpg"
            ),
            "sellPrice": "8.75",
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized["external_id"],
            "CJ-123",
        )

        self.assertEqual(
            normalized["name"],
            "Wireless Charger",
        )

        self.assertEqual(
            normalized["image_url"],
            "https://example.com/image.jpg",
        )

        self.assertEqual(
            normalized["purchase_price"],
            "8.75",
        )

        self.assertEqual(
            normalized["currency"],
            "USD",
        )

    def test_normalizes_product_currency(self):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        product = {
            "id": "CJ-123",
            "nameEn": "Wireless Charger",
            "bigImage": (
                "https://example.com/image.jpg"
            ),
            "sellPrice": "8.75",
            "currency": "USD",
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized["currency"],
            "USD",
        )

    def test_normalizes_product_currency_as_usd_when_missing(
        self,
    ):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        product = {
            "id": "CJ-123",
            "nameEn": "Wireless Charger",
            "bigImage": (
                "https://example.com/image.jpg"
            ),
            "sellPrice": "5.10",
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized["currency"],
            "USD",
        )

    def test_normalize_product_keeps_price_range_as_raw_value(
        self,
    ):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        product = {
            "id": "CJ-123",
            "nameEn": "Wireless Charger",
            "bigImage": (
                "https://example.com/image.jpg"
            ),
            "sellPrice": "2.87 -- 7.23",
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized["purchase_price"],
            "2.87 -- 7.23",
        )

    # ============================================================
    # PRODUCT DETAIL
    # ============================================================

    def test_get_product_detail_sends_expected_request(
        self,
    ):
        class DetailResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": {
                        "id": "CJ-123",
                        "nameEn": (
                            "Wireless Charger"
                        ),
                    },
                }

        class DetailHTTPClient:
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

                return DetailResponse()

        http_client = DetailHTTPClient()

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        client.get_product_detail(
            product_id="CJ-123",
        )

        self.assertEqual(
            http_client.last_params,
            {
                "pid": "CJ-123",
            },
        )

        self.assertEqual(
            http_client.last_headers[
                "CJ-Access-Token"
            ],
            "test-token",
        )

    def test_get_product_detail_returns_product_data(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "id": "CJ-123",
                "nameEn": "Wireless Charger",
                "sellPrice": "8.75",
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        product = client.get_product_detail(
            product_id="CJ-123",
        )

        self.assertEqual(
            product,
            {
                "id": "CJ-123",
                "nameEn": "Wireless Charger",
                "sellPrice": "8.75",
            },
        )

    def test_get_product_detail_returns_none_when_cj_data_is_none(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": False,
            "data": None,
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        product = client.get_product_detail(
            product_id="CJ-123",
        )

        self.assertIsNone(product)

    def test_get_product_detail_returns_none_when_response_json_is_invalid(
        self,
    ):
        response = Mock()

        response.json.side_effect = ValueError(
            "Invalid JSON"
        )

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        product = client.get_product_detail(
            product_id="CJ-123",
        )

        self.assertIsNone(product)

    def test_get_product_detail_returns_none_on_timeout(
        self,
    ):
        http_client = Mock()

        http_client.get.side_effect = (
            httpx.TimeoutException(
                "CJ request timed out"
            )
        )

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        product = client.get_product_detail(
            product_id="CJ-123",
        )

        self.assertIsNone(product)

    def test_get_product_detail_returns_none_when_cj_result_is_false(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 500,
            "result": False,
            "message": "CJ internal error",
            "data": {
                "id": "CJ-123",
                "nameEn": "Wireless Charger",
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        product = client.get_product_detail(
            product_id="CJ-123",
        )

        self.assertIsNone(product)

    # ============================================================
    # PRODUCT VARIANTS
    # ============================================================

    def test_get_product_variants_sends_expected_request(
        self,
    ):
        class VariantsResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": [
                        {
                            "vid": "VARIANT-123",
                            "pid": "CJ-123",
                        }
                    ],
                }

        class VariantsHTTPClient:
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

                return VariantsResponse()

        http_client = VariantsHTTPClient()

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        client.get_product_variants(
            product_id="CJ-123",
        )

        self.assertEqual(
            http_client.last_params,
            {
                "pid": "CJ-123",
            },
        )

        self.assertEqual(
            http_client.last_headers[
                "CJ-Access-Token"
            ],
            "test-token",
        )

    def test_get_product_variants_returns_empty_list_when_cj_data_is_none(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": False,
            "data": None,
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        variants = client.get_product_variants(
            product_id="CJ-123",
        )

        self.assertEqual(
            variants,
            [],
        )

    def test_get_product_variants_returns_empty_list_when_response_json_is_invalid(
        self,
    ):
        response = Mock()

        response.json.side_effect = ValueError(
            "Invalid JSON"
        )

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        variants = client.get_product_variants(
            product_id="CJ-123",
        )

        self.assertEqual(
            variants,
            [],
        )

    def test_get_product_variants_returns_empty_list_on_timeout(
        self,
    ):
        http_client = Mock()

        http_client.get.side_effect = (
            httpx.TimeoutException(
                "CJ request timed out"
            )
        )

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        variants = client.get_product_variants(
            product_id="CJ-123",
        )

        self.assertEqual(
            variants,
            [],
        )

    def test_get_product_variants_returns_empty_list_when_cj_result_is_false(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 500,
            "result": False,
            "message": "CJ internal error",
            "data": [
                {
                    "vid": "VARIANT-123",
                    "pid": "CJ-123",
                }
            ],
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        variants = client.get_product_variants(
            product_id="CJ-123",
        )

        self.assertEqual(
            variants,
            [],
        )

    def test_get_product_variants_returns_empty_list_when_data_is_not_a_list(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "vid": "VARIANT-123",
                "pid": "CJ-123",
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        variants = client.get_product_variants(
            product_id="CJ-123",
        )

        self.assertEqual(
            variants,
            [],
        )

    # ============================================================
    # NORMALIZE VARIANT
    # ============================================================

    def test_normalizes_variant(self):
        client = CJClient(
            access_token="test-token",
            http_client=None,
        )

        variant = {
            "vid": "VARIANT-123",
            "pid": "CJ-123",
            "variantNameEn": "Black",
            "variantSellPrice": "9.25",
        }

        normalized = client.normalize_variant(
            variant
        )

        self.assertEqual(
            normalized,
            {
                "variant_id": "VARIANT-123",
                "product_id": "CJ-123",
                "name": "Black",
                "purchase_price": "9.25",
            },
        )

    # ============================================================
    # VARIANT STOCK
    # ============================================================

    def test_get_variant_stock_sends_expected_request(
        self,
    ):
        class StockResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": [
                        {
                            "vid": "VARIANT-123",
                            "totalInventoryNum": 42,
                        }
                    ],
                }

        class StockHTTPClient:
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

                return StockResponse()

        http_client = StockHTTPClient()

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertEqual(
            http_client.last_params,
            {
                "vid": "VARIANT-123",
            },
        )

        self.assertEqual(
            http_client.last_headers[
                "CJ-Access-Token"
            ],
            "test-token",
        )

    def test_get_variant_stock_returns_total_inventory(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": [
                {
                    "vid": "VARIANT-123",
                    "totalInventoryNum": 42,
                }
            ],
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertEqual(
            stock,
            42,
        )

    def test_get_variant_stock_returns_none_when_no_stock_data(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": [],
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_when_cj_data_is_none(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": False,
            "data": None,
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_when_inventory_field_is_missing(
        self,
    ):
        response = Mock()

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": [
                {
                    "vid": "VARIANT-123",
                }
            ],
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_when_response_json_is_invalid(
        self,
    ):
        response = Mock()

        response.json.side_effect = ValueError(
            "Invalid JSON"
        )

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_on_timeout(
        self,
    ):
        http_client = Mock()

        http_client.get.side_effect = (
            httpx.TimeoutException(
                "CJ request timed out"
            )
        )

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_when_cj_result_is_false(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 500,
            "result": False,
            "message": "CJ internal error",
            "data": [
                {
                    "vid": "VARIANT-123",
                    "totalInventoryNum": 42,
                }
            ],
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_when_data_is_not_a_list(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {
                "vid": "VARIANT-123",
                "totalInventoryNum": 42,
            },
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

    def test_get_variant_stock_returns_none_when_first_item_is_not_a_dict(
        self,
    ):
        response = Mock()
        response.status_code = 200

        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": [
                "unexpected-value",
            ],
        }

        http_client = Mock()
        http_client.get.return_value = response

        client = CJClient(
            access_token="test-token",
            http_client=http_client,
        )

        stock = client.get_variant_stock(
            variant_id="VARIANT-123",
        )

        self.assertIsNone(stock)

        
    