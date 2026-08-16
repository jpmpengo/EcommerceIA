from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    MarketObservationSnapshot,
)


class MarketObservationSnapshotTests(TestCase):

    def test_snapshot_can_be_created_for_observation(self):
        observation = MarketObservation.objects.create(
            source="fake",
            external_id="ABC123",
            name="Support ordinateur portable",
            observed_price=Decimal("19.90"),
            currency="EUR",
        )

        snapshot = MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("19.90"),
            currency="EUR",
        )

        self.assertEqual(
            snapshot.observation,
            observation,
        )

        self.assertEqual(
            snapshot.observed_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            snapshot.currency,
            "EUR",
        )

        self.assertIsNotNone(
            snapshot.observed_at,
        )

        