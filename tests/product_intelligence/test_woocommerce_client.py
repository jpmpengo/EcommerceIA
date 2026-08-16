from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.woocommerce_client import (
    WooCommerceClient,
)


class WooCommerceClientTests(SimpleTestCase):

    def test_get_products_returns_products(self):
        api = Mock()

        response = Mock()
        response.status_code = 200
        response.json.return_value = [
            {
                "id": 123,
                "name": "Wireless Charger",
                "price": "19.90",
                "permalink": (
                    "http://localhost:10004/"
                    "product/wireless-charger/"
                ),
            }
        ]

        api.get.return_value = response

        client = WooCommerceClient(
            api=api,
        )

        products = client.get_products()

        api.get.assert_called_once_with(
            "products"
        )

        self.assertEqual(
            products,
            response.json.return_value,
        )

    def test_normalizes_product(self):
        client = WooCommerceClient(
            api=None,
        )

        product = {
            "id": 123,
            "name": "Wireless Charger",
            "price": "19.90",
            "permalink": (
                "http://localhost:10004/"
                "product/wireless-charger/"
            ),
        }

        normalized = client.normalize_product(
            product
        )

        self.assertEqual(
            normalized,
            {
                "external_id": "123",
                "name": "Wireless Charger",
                "observed_price": "19.90",
                "currency": "EUR",
                "product_url": (
                    "http://localhost:10004/"
                    "product/wireless-charger/"
                ),
            },
        )