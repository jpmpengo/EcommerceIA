from django.test import SimpleTestCase
from product_intelligence.services.opportunity_saturation_score import OpportunitySaturationScoreService


class OpportunitySaturationScoreServiceTests(SimpleTestCase):
    def test_saturation_levels(self):
        cases = [("very_low", 30), ("low", 24), ("moderate", 18), ("high", 9), ("very_high", 0), ("indeterminate", None)]
        for level, expected in cases:
            with self.subTest(level=level):
                self.assertEqual(OpportunitySaturationScoreService.calculate(level), expected)
