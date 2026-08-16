from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
)

from django.db import IntegrityError

class MarketObservationTests(TestCase):

    def test_market_observation_can_be_created(self):
        observation = MarketObservation.objects.create(
            source="test_source",
            external_id="ABC123",
            name="Support ordinateur portable",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url=(
                "https://example.com/products/ABC123"
            ),
        )

        self.assertEqual(
            observation.source,
            "test_source",
        )

        self.assertEqual(
            observation.external_id,
            "ABC123",
        )

        self.assertEqual(
            observation.name,
            "Support ordinateur portable",
        )

        self.assertEqual(
            observation.observed_price,
            Decimal("19.90"),
        )

    def test_same_source_and_external_id_cannot_be_duplicated(self):
        MarketObservation.objects.create(
            source="test_source",
            external_id="ABC123",
            name="Premier produit",
        )

        with self.assertRaises(IntegrityError):
            MarketObservation.objects.create(
                source="test_source",
                external_id="ABC123",
                name="Même produit récupéré à nouveau",
            )
        
    def test_different_sources_can_share_same_external_id(self):
        first = MarketObservation.objects.create(
            source="source_a",
            external_id="ABC123",
            name="Produit A",
        )

        second = MarketObservation.objects.create(
            source="source_b",
            external_id="ABC123",
            name="Produit B",
        )

        self.assertNotEqual(
            first.id,
            second.id,
        )

        self.assertEqual(
            MarketObservation.objects.count(),
            2,
        )

