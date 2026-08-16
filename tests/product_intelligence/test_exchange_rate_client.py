from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)


class FakeResponse:

    def json(self):
        return {
            "result": "success",
            "base_code": "USD",
            "rates": {
                "EUR": 0.86,
            },
        }


class FakeHTTPClient:

    def __init__(self):
        self.last_url = None

    def get(self, url):
        self.last_url = url
        return FakeResponse()


class ExchangeRateClientTests(SimpleTestCase):

    def test_gets_exchange_rate(self):
        http_client = FakeHTTPClient()

        client = ExchangeRateClient(
            http_client=http_client,
        )

        rate = client.get_rate(
            from_currency="USD",
            to_currency="EUR",
        )

        self.assertEqual(
            rate,
            Decimal("0.86"),
        )

        self.assertEqual(
            http_client.last_url,
            "https://open.er-api.com/v6/latest/USD",
        )

    def test_returns_one_when_currencies_match(self):
        http_client = FakeHTTPClient()

        client = ExchangeRateClient(
            http_client=http_client,
        )

        rate = client.get_rate(
            from_currency="EUR",
            to_currency="EUR",
        )

        self.assertEqual(
            rate,
            Decimal("1"),
        )

        self.assertIsNone(
            http_client.last_url,
        )

    def test_raises_clear_error_when_rate_is_missing(self):
        class MissingRateResponse:

            def json(self):
                return {
                    "result": "success",
                    "base_code": "USD",
                    "rates": {},
                }

        class MissingRateHTTPClient:

            def get(self, url):
                return MissingRateResponse()

        client = ExchangeRateClient(
            http_client=MissingRateHTTPClient(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "Exchange rate EUR not found for USD.",
        ):
            client.get_rate(
                from_currency="USD",
                to_currency="EUR",
            )

            