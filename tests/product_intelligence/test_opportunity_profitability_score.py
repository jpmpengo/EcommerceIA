from decimal import Decimal
from django.test import SimpleTestCase
from product_intelligence.services.opportunity_profitability_score import OpportunityProfitabilityScoreService


class OpportunityProfitabilityScoreServiceTests(SimpleTestCase):
    def test_profitability_score_thresholds(self):
        cases = [("10.00", 10), ("20.00", 20), ("30.00", 30), ("40.00", 35), ("50.00", 38), ("60.00", 40)]
        for margin, expected in cases:
            with self.subTest(margin=margin):
                self.assertEqual(OpportunityProfitabilityScoreService.calculate(Decimal(margin)), expected)

    def test_interpolation_and_limits(self):
        cases = [("5.00", 0), ("15.00", 15), ("35.00", 33), ("75.00", 40)]
        for margin, expected in cases:
            with self.subTest(margin=margin):
                self.assertEqual(OpportunityProfitabilityScoreService.calculate(Decimal(margin)), expected)
