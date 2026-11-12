from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.eprolo_shipping_estimator import (
    EproloShippingEstimator,
)


class EproloShippingEstimatorTests(SimpleTestCase):

    def test_selects_cheapest_recent_rate_under_delivery_limit(self):
        client = Mock()
        client.get_shipping_rates.return_value = [
            {
                "cost": 16.54,
                "shiptime": "20-60 days",
                "ship_method": "PostNL",
                "updatetime": "2025-11-28 09:57:36.0",
            },
            {
                "cost": 12.54,
                "shiptime": "6-10 Days",
                "ship_method": "Colissimo",
                "updatetime": "2025-03-11 18:03:46.0",
            },
            {
                "cost": 9.33,
                "shiptime": "8-12 Days",
                "ship_method": "Stale rate",
                "updatetime": "2020-11-09 15:13:20.0",
            },
        ]
        offer = Mock(
            supplier_parent_product_id="32552962",
            supplier_product_id="729665812",
        )
        estimator = EproloShippingEstimator(
            client=client,
            maximum_shipping_days=20,
            maximum_rate_age_days=730,
            now_factory=lambda: datetime(
                2026, 9, 2, tzinfo=timezone.utc
            ),
        )

        quote = estimator.estimate(
            offer=offer,
            destination_country="FR",
            quantity=2,
        )

        self.assertEqual(quote["cost"], Decimal("25.08"))
        self.assertEqual(quote["shipping_days"], 10)
        self.assertEqual(quote["method"], "Colissimo")
        self.assertEqual(quote["currency"], "USD")

    def test_handles_only_eprolo(self):
        offer = Mock()
        offer.supplier.name = "EPROLO"
        self.assertTrue(EproloShippingEstimator.can_handle(offer))
        offer.supplier.name = "CJdropshipping"
        self.assertFalse(EproloShippingEstimator.can_handle(offer))
