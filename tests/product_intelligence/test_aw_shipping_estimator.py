from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.aw_shipping_estimator import (
    AWShippingEstimator,
)


class AWShippingEstimatorTests(SimpleTestCase):

    def test_estimates_france_shipping_for_230_grams(self):
        offer = Mock()
        offer.supplier.name = "AW Dropship"
        offer.shipping_weight_grams = 230

        estimator = AWShippingEstimator()

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("7.50"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            },
        )

    def test_estimates_france_shipping_up_to_2kg(self):
        offer = Mock()
        offer.supplier.name = "AW Dropship"
        offer.shipping_weight_grams = 500

        estimator = AWShippingEstimator()

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("7.80"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            },
        )

    def test_estimates_france_shipping_up_to_5kg(self):
        offer = Mock()
        offer.supplier.name = "AW Dropship"
        offer.shipping_weight_grams = 3000

        estimator = AWShippingEstimator()

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("12.90"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            },
        )

    def test_estimates_france_shipping_up_to_30kg(self):
        offer = Mock()
        offer.supplier.name = "AW Dropship"
        offer.shipping_weight_grams = 10000

        estimator = AWShippingEstimator()

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("13.20"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            },
        )

    def test_returns_none_above_30kg(self):
        offer = Mock()
        offer.supplier.name = "AW Dropship"
        offer.shipping_weight_grams = 31000

        estimator = AWShippingEstimator()

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertIsNone(result)

