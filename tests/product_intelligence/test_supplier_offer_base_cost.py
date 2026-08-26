from datetime import (
    datetime,
    timezone,
)
from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)
from product_intelligence.services.supplier_offer_base_cost import (
    SupplierOfferBaseCostService,
)


class SupplierOfferBaseCostServiceTests(
    SimpleTestCase
):

    def test_converts_purchase_and_shipping_cost(
        self,
    ):
        supplier_offer = Mock()
        supplier_offer.purchase_price = (
            Decimal("5.01")
        )
        supplier_offer.shipping_cost = (
            Decimal("13.32")
        )
        supplier_offer.currency = "USD"

        rate_client = Mock()
        rate_client.BASE_URL = (
            "https://rates.example.test"
        )
        rate_client.get_rate.return_value = (
            Decimal("0.92")
        )

        calculated_at = datetime(
            2026,
            8,
            26,
            15,
            0,
            tzinfo=timezone.utc,
        )

        service = SupplierOfferBaseCostService(
            rate_client=rate_client,
            conversion_service=(
                CurrencyConversionService()
            ),
            clock=lambda: calculated_at,
        )

        result = service.calculate(
            supplier_offer=supplier_offer,
            target_currency="EUR",
        )

        rate_client.get_rate.assert_called_once_with(
            from_currency="USD",
            to_currency="EUR",
        )

        self.assertEqual(
            result,
            {
                "source_currency": "USD",
                "target_currency": "EUR",
                "exchange_rate": Decimal("0.92"),
                "purchase_original": Decimal("5.01"),
                "shipping_original": Decimal("13.32"),
                "purchase_converted": Decimal("4.61"),
                "shipping_converted": Decimal("12.25"),
                "base_cost": Decimal("16.86"),
                "rate_source": (
                    "https://rates.example.test"
                ),
                "calculated_at": calculated_at,
            },
        )

    def test_does_not_request_rate_for_same_currency(
        self,
    ):
        supplier_offer = Mock()
        supplier_offer.purchase_price = (
            Decimal("5.00")
        )
        supplier_offer.shipping_cost = (
            Decimal("2.50")
        )
        supplier_offer.currency = "EUR"

        rate_client = Mock()

        service = SupplierOfferBaseCostService(
            rate_client=rate_client,
            conversion_service=(
                CurrencyConversionService()
            ),
        )

        result = service.calculate(
            supplier_offer=supplier_offer,
            target_currency="EUR",
        )

        rate_client.get_rate.assert_not_called()

        self.assertEqual(
            result["exchange_rate"],
            Decimal("1"),
        )

        self.assertEqual(
            result["base_cost"],
            Decimal("7.50"),
        )

    def test_rejects_missing_shipping_cost(
        self,
    ):
        supplier_offer = Mock()
        supplier_offer.purchase_price = (
            Decimal("5.01")
        )
        supplier_offer.shipping_cost = None
        supplier_offer.currency = "USD"

        service = SupplierOfferBaseCostService(
            rate_client=Mock(),
            conversion_service=(
                CurrencyConversionService()
            ),
        )

        with self.assertRaisesMessage(
            ValueError,
            "Coût de livraison manquant.",
        ):
            service.calculate(
                supplier_offer=supplier_offer,
                target_currency="EUR",
            )