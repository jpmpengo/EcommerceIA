from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.printful_shipping_estimator import (
    PrintfulShippingEstimator,
)


class PrintfulShippingEstimatorTests(
    SimpleTestCase
):

    def test_returns_cheapest_standard_rate_to_destination(
        self,
    ):
        offer = Mock()
        offer.supplier.name = "Printful"
        offer.supplier_product_id = "14942"
        offer.currency = "USD"

        client = Mock()
        client.get_shipping_rates.return_value = [
            {
                "shipping": "STANDARD",
                "shipping_method_name": "Flat Rate",
                "rate": "7.49",
                "currency": "USD",
                "max_delivery_days": 8,
            },
            {
                "shipping": "EXPRESS",
                "shipping_method_name": "Express",
                "rate": "18.00",
                "currency": "USD",
                "max_delivery_days": 3,
            },
        ]

        estimator = PrintfulShippingEstimator(
            client=client,
        )

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        client.get_shipping_rates.assert_called_once_with(
            variant_id=14942,
            destination_country="FR",
            quantity=1,
            currency="USD",
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("7.49"),
                "currency": "USD",
                "shipping_days": 8,
                "shipping_country": "FR",
                "method": "Flat Rate",
            },
        )
