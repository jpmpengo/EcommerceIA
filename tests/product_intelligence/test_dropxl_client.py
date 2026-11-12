from unittest.mock import Mock
from requests.auth import HTTPBasicAuth
from django.test import SimpleTestCase
from product_intelligence.services.dropxl_client import DropXLClient


class DropXLClientTests(SimpleTestCase):
    def test_gets_catalog_page_with_basic_auth(self):
        response = Mock()
        response.json.return_value = {"data": [{"id": 123, "code": "TEST-123", "price": "19.95", "currency": "EUR"}], "pagination": {"offset": 0, "limit": 1, "total": 22706}}
        http_client = Mock()
        http_client.get.return_value = response
        client = DropXLClient(api_email="test@example.com", api_token="test-token", sandbox_mode=True, http_client=http_client)
        products = client.get_products(limit=1, offset=0)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["code"], "TEST-123")
        http_client.get.assert_called_once_with("https://sandbox.b2b.dropxl.com/api_customer/products", params={"limit": 1, "offset": 0}, auth=HTTPBasicAuth("test@example.com", "test-token"), timeout=30)
        response.raise_for_status.assert_called_once_with()

    def test_uses_production_url(self):
        response = Mock()
        response.json.return_value = {"data": []}
        http_client = Mock()
        http_client.get.return_value = response
        client = DropXLClient(api_email="test@example.com", api_token="test-token", sandbox_mode=False, http_client=http_client)
        client.get_products(limit=2, offset=10)
        self.assertEqual(http_client.get.call_args.args[0], "https://b2b.dropxl.com/api_customer/products")
        self.assertEqual(http_client.get.call_args.kwargs["params"], {"limit": 2, "offset": 10})
