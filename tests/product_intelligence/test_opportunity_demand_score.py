from django.test import SimpleTestCase
from product_intelligence.services.opportunity_demand_score import OpportunityDemandScoreService


class OpportunityDemandScoreServiceTests(SimpleTestCase):
    def test_demand_score_conversion(self):
        cases = [(0, 0), (46, 14), (62, 19), (65, 20), (90, 27), (100, 30)]
        for demand_score, expected in cases:
            with self.subTest(demand_score=demand_score):
                self.assertEqual(OpportunityDemandScoreService.calculate(demand_score), expected)
