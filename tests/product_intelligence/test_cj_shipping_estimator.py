from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.cj_shipping_estimator import (
    CJShippingEstimator,
)


class CJShippingEstimatorTests(
    SimpleTestCase
):

    def test_returns_cheapest_freight_option_to_destination(
        self,
    ):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-VARIANT-1"

        client = Mock()
        client.calculate_freight.return_value = [
            {
                "logisticName": "Fast Express",
                "logisticPrice": 12.00,
                "logisticAging": "4-7",
            },
            {
                "logisticName": "CJPacket",
                "logisticPrice": 6.25,
                "logisticAging": "8-15",
            },
        ]

        estimator = CJShippingEstimator(
            client=client,
            origin_country="CN",
        )

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        client.calculate_freight.assert_called_once_with(
            variant_id="CJ-VARIANT-1",
            origin_country="CN",
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("6.25"),
                "currency": "USD",
                "shipping_days": 15,
                "shipping_country": "FR",
                "method": "CJPacket",
            },
        )
