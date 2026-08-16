from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.opportunity_score_service import (
    OpportunityScoreService,
)


class OpportunityScoreServiceTests(SimpleTestCase):

    def test_price_decrease_scores_higher_than_stable_price(self):
        decrease_signals = {
            "previous_price": Decimal("19.90"),
            "current_price": Decimal("17.50"),
            "price_change": Decimal("-2.40"),
            "price_change_percent": Decimal("-12.06"),
            "direction": "down",
        }

        stable_signals = {
            "previous_price": Decimal("19.90"),
            "current_price": Decimal("19.90"),
            "price_change": Decimal("0.00"),
            "price_change_percent": Decimal("0.00"),
            "direction": "stable",
        }

        decrease_score = OpportunityScoreService.calculate(
            decrease_signals
        )

        stable_score = OpportunityScoreService.calculate(
            stable_signals
        )

        self.assertGreater(
            decrease_score,
            stable_score,
        )

    def test_price_increase_scores_lower_than_stable_price(self):
        increase_signals = {
            "previous_price": Decimal("20.00"),
            "current_price": Decimal("22.00"),
            "price_change": Decimal("2.00"),
            "price_change_percent": Decimal("10.00"),
            "direction": "up",
        }

        stable_signals = {
            "previous_price": Decimal("20.00"),
            "current_price": Decimal("20.00"),
            "price_change": Decimal("0.00"),
            "price_change_percent": Decimal("0.00"),
            "direction": "stable",
        }

        increase_score = OpportunityScoreService.calculate(
            increase_signals
        )

        stable_score = OpportunityScoreService.calculate(
            stable_signals
        )

        self.assertLess(
            increase_score,
            stable_score,
        )

    def test_score_is_clamped_between_zero_and_one_hundred(self):
        very_large_drop = {
            "previous_price": Decimal("100.00"),
            "current_price": Decimal("1.00"),
            "price_change": Decimal("-99.00"),
            "price_change_percent": Decimal("-99.00"),
            "direction": "down",
        }

        very_large_increase = {
            "previous_price": Decimal("1.00"),
            "current_price": Decimal("100.00"),
            "price_change": Decimal("99.00"),
            "price_change_percent": Decimal("9900.00"),
            "direction": "up",
        }

        high_score = OpportunityScoreService.calculate(
            very_large_drop
        )

        low_score = OpportunityScoreService.calculate(
            very_large_increase
        )

        self.assertGreaterEqual(
            high_score,
            Decimal("0.00"),
        )

        self.assertLessEqual(
            high_score,
            Decimal("100.00"),
        )

        self.assertGreaterEqual(
            low_score,
            Decimal("0.00"),
        )

        self.assertLessEqual(
            low_score,
            Decimal("100.00"),
        )

    def test_explain_returns_reason_for_price_decrease(self):
        signals = {
            "previous_price": Decimal("19.90"),
            "current_price": Decimal("17.50"),
            "price_change": Decimal("-2.40"),
            "price_change_percent": Decimal("-12.06"),
            "direction": "down",
        }

        result = OpportunityScoreService.explain(
            signals
        )

        self.assertEqual(
            result["score"],
            Decimal("62.06"),
        )

        self.assertIn(
            "Baisse de prix de 12.06 %",
            result["reasons"],
        )

        