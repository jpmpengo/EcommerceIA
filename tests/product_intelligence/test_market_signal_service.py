from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    MarketObservationSnapshot,
)

from product_intelligence.services.market_signal_service import (
    MarketSignalService,
)


class MarketSignalServiceTests(TestCase):

    def test_detects_price_decrease(self):
        observation = MarketObservation.objects.create(
            source="fake",
            external_id="ABC123",
            name="Support ordinateur portable",
            observed_price=Decimal("17.50"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("19.90"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("17.50"),
            currency="EUR",
        )

        signals = MarketSignalService.analyze(
            observation
        )

        self.assertEqual(
            signals["previous_price"],
            Decimal("19.90"),
        )

        self.assertEqual(
            signals["current_price"],
            Decimal("17.50"),
        )

        self.assertEqual(
            signals["price_change"],
            Decimal("-2.40"),
        )

        self.assertEqual(
            signals["direction"],
            "down",
        )

    def test_calculates_price_change_percentage(self):
        observation = MarketObservation.objects.create(
            source="fake",
            external_id="ABC123",
            name="Support ordinateur portable",
            observed_price=Decimal("17.50"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("19.90"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("17.50"),
            currency="EUR",
        )

        signals = MarketSignalService.analyze(
            observation
        )

        self.assertEqual(
            signals["price_change_percent"],
            Decimal("-12.06"),
        )
    
    def test_detects_price_increase(self):
        observation = MarketObservation.objects.create(
            source="fake",
            external_id="UP123",
            name="Produit en hausse",
            observed_price=Decimal("22.00"),
            currency="EUR",
        )   

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("20.00"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("22.00"),
            currency="EUR",
        )

        signals = MarketSignalService.analyze(
            observation
        )

        self.assertEqual(
            signals["previous_price"],
            Decimal("20.00"),
        )

        self.assertEqual(
            signals["current_price"],
            Decimal("22.00"),
        )

        self.assertEqual(
            signals["price_change"],
            Decimal("2.00"),
        )

        self.assertEqual(
            signals["price_change_percent"],
            Decimal("10.00"),
        )

        self.assertEqual(
            signals["direction"],
            "up",
        )

    def test_detects_stable_price(self):
        observation = MarketObservation.objects.create(
            source="fake",
            external_id="STABLE123",
            name="Produit stable",
            observed_price=Decimal("20.00"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("20.00"),
            currency="EUR",
        )

        MarketObservationSnapshot.objects.create(
            observation=observation,
            observed_price=Decimal("20.00"),
            currency="EUR",
        )

        signals = MarketSignalService.analyze(
            observation
        )

        self.assertEqual(
            signals["price_change"],
            Decimal("0.00"),
        )

        self.assertEqual(
            signals["price_change_percent"],
            Decimal("0.00"),
        )

        self.assertEqual(
            signals["direction"],
            "stable",
        )

    