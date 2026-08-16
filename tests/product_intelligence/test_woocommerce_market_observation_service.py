from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import MarketObservation
from product_intelligence.services.woocommerce_market_observation import (
    WooCommerceMarketObservationService,
)


class WooCommerceMarketObservationServiceTests(TestCase):

    def test_creates_market_observation_from_normalized_product(self):
        service = WooCommerceMarketObservationService()

        product = {
            "external_id": "123",
            "name": "Wireless Charger",
            "observed_price": "19.90",
            "currency": "EUR",
            "product_url": (
                "http://localhost:10004/"
                "product/wireless-charger/"
            ),
        }

        observation = service.create_observation(
            product=product,
        )

        self.assertIsInstance(
            observation,
            MarketObservation,
        )

        self.assertEqual(
            observation.source,
            "woocommerce",
        )

        self.assertEqual(
            observation.external_id,
            "123",
        )

        self.assertEqual(
            observation.name,
            "Wireless Charger",
        )

        self.assertEqual(
            observation.observed_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            observation.currency,
            "EUR",
        )

        self.assertEqual(
            observation.product_url,
            (
                "http://localhost:10004/"
                "product/wireless-charger/"
            ),
        )

        self.assertEqual(
            observation.raw_data,
            product,
        )

    def test_updates_existing_observation_for_same_product(self):
        service = WooCommerceMarketObservationService()

        product = {
            "external_id": "123",
            "name": "Wireless Charger",
            "observed_price": "19.90",
            "currency": "EUR",
            "product_url": (
                "http://localhost:10004/"
                "product/wireless-charger/"
            ),
        }

        first_observation = service.create_observation(
            product=product,
        )

        product["observed_price"] = "24.90"

        second_observation = service.create_observation(
            product=product,
        )

        self.assertEqual(
            first_observation.id,
            second_observation.id,
        )

        self.assertEqual(
            MarketObservation.objects.filter(
                source="woocommerce",
                external_id="123",
            ).count(),
            1,
        )

        second_observation.refresh_from_db()

        self.assertEqual(
            second_observation.observed_price,
            Decimal("24.90"),
        )