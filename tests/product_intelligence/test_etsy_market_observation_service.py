from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import MarketObservation
from product_intelligence.services.etsy_market_observation import (
    EtsyMarketObservationService,
)


class EtsyMarketObservationServiceTests(TestCase):

    def test_creates_market_observation_from_normalized_listing(self):
        service = EtsyMarketObservationService()

        listing = {
            "external_id": "123456789",
            "name": "Wireless Charger",
            "observed_price": "19.90",
            "currency": "EUR",
            "product_url": "https://www.etsy.com/listing/123456789",
        }

        observation = service.create_observation(
            listing=listing,
        )

        self.assertIsInstance(
            observation,
            MarketObservation,
        )

        self.assertEqual(
            observation.source,
            "etsy",
        )

        self.assertEqual(
            observation.external_id,
            "123456789",
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
            "https://www.etsy.com/listing/123456789",
        )

    def test_updates_existing_observation_for_same_listing(self):
        service = EtsyMarketObservationService()

        first_listing = {
            "external_id": "123456789",
            "name": "Wireless Charger",
            "observed_price": "19.90",
            "currency": "EUR",
            "product_url": "https://www.etsy.com/listing/123456789",
        }

        first_observation = service.create_observation(
            listing=first_listing,
        )

        updated_listing = {
            "external_id": "123456789",
            "name": "Wireless Charger",
            "observed_price": "17.90",
            "currency": "EUR",
            "product_url": "https://www.etsy.com/listing/123456789",
        }

        second_observation = service.create_observation(
            listing=updated_listing,
        )

        self.assertEqual(
            first_observation.id,
            second_observation.id,
        )

        second_observation.refresh_from_db()

        self.assertEqual(
            second_observation.observed_price,
            Decimal("17.90"),
        )

        self.assertEqual(
            MarketObservation.objects.filter(
                source="etsy",
                external_id="123456789",
            ).count(),
            1,
        )
