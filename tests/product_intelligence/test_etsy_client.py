from unittest import TestCase
from unittest.mock import Mock

from product_intelligence.services.etsy_client import EtsyClient


class EtsyClientTests(TestCase):

    def test_get_listing_sends_api_key(self):
        http_client = Mock()

        response = Mock()
        response.json.return_value = {
            "listing_id": 123456789,
            "title": "Wireless Charger",
        }
        response.raise_for_status.return_value = None

        http_client.get.return_value = response

        client = EtsyClient(
            api_key="test-etsy-key",
            shared_secret="test-etsy-secret",
            http_client=http_client,
        )

        client.get_listing(
            listing_id=123456789,
        )

        http_client.get.assert_called_once_with(
            "https://openapi.etsy.com/v3/application/listings/123456789",
            headers={
                "x-api-key": "test-etsy-key:test-etsy-secret",
            },
        )

    def test_get_listing_returns_listing_data(self):
        http_client = Mock()

        response = Mock()
        response.json.return_value = {
            "listing_id": 123456789,
            "title": "Wireless Charger",
            "price": {
                "amount": 1990,
                "divisor": 100,
                "currency_code": "EUR",
            },
            "url": "https://www.etsy.com/listing/123456789",
        }
        response.raise_for_status.return_value = None

        http_client.get.return_value = response

        client = EtsyClient(
            api_key="test-etsy-key",
            shared_secret="test-etsy-secret",
            http_client=http_client,
        )

        listing = client.get_listing(
            listing_id=123456789,
        )

        self.assertEqual(
            listing["listing_id"],
            123456789,
        )

        self.assertEqual(
            listing["title"],
            "Wireless Charger",
        )

        self.assertEqual(
            listing["price"]["currency_code"],
            "EUR",
        )

    def test_normalizes_listing(self):
        client = EtsyClient(
            api_key="test-etsy-key",
            shared_secret="test-etsy-secret",
            http_client=None,
        )

        listing = {
            "listing_id": 123456789,
            "title": "Wireless Charger",
            "price": {
                "amount": 1990,
                "divisor": 100,
                "currency_code": "EUR",
            },
            "url": "https://www.etsy.com/listing/123456789",
        }

        normalized = client.normalize_listing(listing)

        self.assertEqual(
            normalized,
            {
                "external_id": "123456789",
                "name": "Wireless Charger",
                "observed_price": "19.90",
                "currency": "EUR",
                "product_url": "https://www.etsy.com/listing/123456789",
            },
        )

    def test_ping_sends_api_credentials(self):
        http_client = Mock()

        response = Mock()
        response.json.return_value = {
            "application_id": 123456,
        }
        response.raise_for_status.return_value = None

        http_client.get.return_value = response

        client = EtsyClient(
            api_key="test-etsy-key",
            shared_secret="test-etsy-secret",
            http_client=http_client,
        )

        result = client.ping()

        http_client.get.assert_called_once_with(
            "https://openapi.etsy.com/v3/application/openapi-ping",
            headers={
                "x-api-key": "test-etsy-key:test-etsy-secret",
            },
        )

        self.assertEqual(
            result,
            {
                "application_id": 123456,
            },
        )