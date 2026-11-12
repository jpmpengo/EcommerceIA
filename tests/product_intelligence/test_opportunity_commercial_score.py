from decimal import Decimal
from django.test import SimpleTestCase
from product_intelligence.services.opportunity_commercial_score import OpportunityCommercialScoreService


class OpportunityCommercialScoreServiceTests(SimpleTestCase):
    def test_complete_score(self):
        self.assertEqual(OpportunityCommercialScoreService.calculate(Decimal("30"), 65, "moderate"), 68)

    def test_very_high_saturation_is_zero_not_missing(self):
        self.assertEqual(OpportunityCommercialScoreService.calculate(Decimal("30"), 65, "very_high"), 50)

    def test_indeterminate_saturation_has_no_final_score(self):
        self.assertIsNone(OpportunityCommercialScoreService.calculate(Decimal("30"), 65, "indeterminate"))
