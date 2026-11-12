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

    def test_prefers_cheapest_option_within_maximum_delay(
        self,
    ):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-VARIANT-1"

        client = Mock()
        client.calculate_freight.return_value = [
            {
                "logisticName": "CJPacket Eub",
                "logisticPrice": "4.87",
                "logisticAging": "12-50",
            },
            {
                "logisticName": (
                    "CJPacket Ordinary I"
                ),
                "logisticPrice": "5.19",
                "logisticAging": "8-18",
            },
            {
                "logisticName": "Fast Express",
                "logisticPrice": "9.43",
                "logisticAging": "4-7",
            },
        ]

        estimator = CJShippingEstimator(
            client=client,
            maximum_shipping_days=20,
        )

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("5.19"),
                "currency": "USD",
                "shipping_days": 18,
                "shipping_country": "FR",
                "method": (
                    "CJPacket Ordinary I"
                ),
            },
        )

    def test_prefers_route_with_eu_duties_included_over_ddu_route(self):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-VARIANT-1"
        offer.supplier_parent_product_id = "CJ-PRODUCT-1"
        offer.shipping_weight_grams = 730
        offer.stock_country = "CN"
        offer.free_shipping = False

        client = Mock()
        client.calculate_freight.return_value = [
            {
                "logisticName": "DDU Route",
                "totalPostageFee": "11.00",
                "logisticAging": "8-15",
            },
        ]
        client.get_product_detail.return_value = {
            "productSku": "CJXFLPJY00201",
            "productProEnSet": ["COMMON"],
        }
        client.calculate_freight_tip.return_value = [
            {
                "arrivalTime": "8-18",
                "totalPostageFee": 12.20,
                "option": {
                    "enName": "CJPacket Ordinary I",
                    "cnName": "急速普货（欧盟包税）",
                },
                "message": "",
                "tariff": None,
            },
            {
                "arrivalTime": "12-50",
                "totalPostageFee": 10.00,
                "option": {
                    "enName": "CJPacket Eub",
                    "cnName": "CJ义乌EUB",
                },
                "message": "DDU Custom Clearance, buyer pays duties and taxes",
                "tariff": 0.0,
            },
        ]

        estimator = CJShippingEstimator(client=client, maximum_shipping_days=20)
        result = estimator.estimate(offer=offer, destination_country="FR")

        self.assertEqual(result["method"], "CJPacket Ordinary I")
        self.assertEqual(result["cost"], Decimal("12.20"))
        self.assertEqual(result["shipping_days"], 18)
        self.assertTrue(result["customs_included"])

    def test_returns_zero_cost_without_inventing_delay_for_explicit_free_shipping(self):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-FREE-VARIANT"
        offer.free_shipping = True
        offer.stock_country = "DE"

        client = Mock()
        client.calculate_freight.return_value = []

        estimator = CJShippingEstimator(
            client=client,
            origin_country="CN",
        )

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            {
                "cost": Decimal("0"),
                "currency": "USD",
                "shipping_days": None,
                "shipping_country": "FR",
                "method": "Free shipping included",
            },
        )

    def test_uses_freight_tip_delay_for_explicit_free_shipping(self):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-FREE-VARIANT"
        offer.supplier_parent_product_id = "1990724491834609666"
        offer.shipping_weight_grams = 608
        offer.free_shipping = True
        offer.stock_country = "DE"

        client = Mock()
        client.calculate_freight.return_value = []
        client.get_product_detail.return_value = {
            "productSku": "CJYD2604897",
            "productProEnSet": ["COMMON"],
        }
        client.calculate_freight_tip.return_value = [
            {
                "arrivalTime": "5-9",
                "logisticName": "Supplier Logistics",
            }
        ]

        estimator = CJShippingEstimator(client=client)

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
        )

        self.assertEqual(result["cost"], Decimal("0"))
        self.assertEqual(result["shipping_days"], 9)

    def test_does_not_assume_free_shipping_when_explicitly_false(self):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-NOT-FREE"
        offer.free_shipping = False
        offer.stock_country = "DE"

        client = Mock()
        client.calculate_freight.return_value = []

        estimator = CJShippingEstimator(client=client)

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
        )

        self.assertIsNone(result)

    def test_does_not_assume_free_shipping_when_unknown(self):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-UNKNOWN-FREE"
        offer.free_shipping = None
        offer.stock_country = "DE"

        client = Mock()
        client.calculate_freight.return_value = []

        estimator = CJShippingEstimator(client=client)

        result = estimator.estimate(
            offer=offer,
            destination_country="FR",
        )

        self.assertIsNone(result)

    def test_uses_offer_stock_country_as_origin(self):
        offer = Mock()
        offer.supplier.name = "CJdropshipping"
        offer.supplier_product_id = "CJ-VARIANT-DE"
        offer.stock_country = "DE"
        client = Mock()
        client.calculate_freight.return_value = [{"logisticName":"EU","logisticPrice":"4.00","logisticAging":"2-4"}]
        estimator = CJShippingEstimator(client=client, origin_country="CN")
        estimator.estimate(offer=offer, destination_country="FR", quantity=1)
        client.calculate_freight.assert_called_once_with(variant_id="CJ-VARIANT-DE", origin_country="DE", destination_country="FR", quantity=1)
