from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.aw_client import AWClient


class AWClientTests(SimpleTestCase):

    def test_searches_products_with_bearer_auth(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "data": [
                {
                    "id": 188999,
                    "code": "MacP-03",
                    "name": "Macrame Pot Holder - Lrg Single Beaded",
                    "price": "10.96",
                    "current_stock": 128,
                    "gross_weight": 230,
                    "currency_code": "EUR",
                }
            ]
        }
        http_client = Mock()
        http_client.get.return_value = response

        client = AWClient(
            api_token="test-token",
            http_client=http_client,
        )

        products = client.search_products("planter")

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["id"], 188999)
        self.assertEqual(products[0]["gross_weight"], 230)
        http_client.get.assert_called_once_with(
            "https://api.aiku.io/dropshipping/products",
            params={
                "search": "planter",
                "include": "department,sub_department,family",
            },
            headers={
                "Authorization": "Bearer test-token",
                "Accept": "application/json",
                "User-Agent": "EcommerceIA/1.0",
            },
        )

    def test_uses_configured_base_url(self):
        response = Mock(status_code=200)
        response.json.return_value = {"data": []}
        http_client = Mock()
        http_client.get.return_value = response

        client = AWClient(
            api_token="test-token",
            api_base_url="https://api.aiku-sandbox.uk",
            http_client=http_client,
        )

        client.search_products("planter")

        url = http_client.get.call_args.args[0]
        self.assertEqual(
            url,
            "https://api.aiku-sandbox.uk/dropshipping/products",
        )
