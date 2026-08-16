from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)


class CurrencyConversionServiceTests(SimpleTestCase):

    def test_converts_usd_to_eur(self):
        service = CurrencyConversionService()

        result = service.convert(
            amount=Decimal("7.30"),
            from_currency="USD",
            to_currency="EUR",
            exchange_rate=Decimal("0.86"),
        )

        self.assertEqual(
            result,
            Decimal("6.28"),
        )

    def test_returns_same_amount_when_currency_matches(self):
        service = CurrencyConversionService()

        result = service.convert(
            amount=Decimal("7.30"),
            from_currency="EUR",
            to_currency="EUR",
            exchange_rate=Decimal("0.86"),
        )

        self.assertEqual(
            result,
            Decimal("7.30"),
        )

    def test_rounds_result_to_two_decimal_places(self):
        service = CurrencyConversionService()

        result = service.convert(
            amount=Decimal("7.30"),
            from_currency="USD",
            to_currency="EUR",
            exchange_rate=Decimal("0.8675"),
        )

        self.assertEqual(
            result,
            Decimal("6.33"),
        )
        