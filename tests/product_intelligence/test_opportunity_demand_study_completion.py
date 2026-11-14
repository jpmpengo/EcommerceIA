from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch
from product_intelligence.services.opportunity_demand_study_completion import OpportunityDemandStudyCompletionService


class OpportunityDemandStudyCompletionTests(TestCase):
    @patch("product_intelligence.services.opportunity_commercial_score.OpportunityCommercialScoreService.calculate", return_value=50)
    @patch("product_intelligence.services.demand_score_service.DemandScoreService.calculate", return_value=20)
    @patch("product_intelligence.services.opportunity_demand_study_completion.ProductIdeaScoreService.calculate", return_value=30)
    @patch("product_intelligence.services.opportunity_demand_study_completion.ProductIdeaGenerationService._verify_growth_signals")
    @patch("product_intelligence.services.opportunity_demand_evidence_search.OpportunityDemandEvidenceSearchService.search")
    def test_only_verified_new_evidence_is_saved(self, search, verify, score, demand, commercial):
        valid = {"metric": "sales_growth", "value": "Croissance documentee", "source_url": "https://example.com/valid"}
        invalid = {"metric": "sales_growth", "value": "Croissance non confirmee", "source_url": "https://example.com/invalid"}
        search.return_value = [valid, invalid]
        verify.return_value = [dict(valid, is_verified=True), dict(invalid, is_verified=False)]
        idea = SimpleNamespace(demand_signal_assessments=[], idea_score=0, save=MagicMock())
        offer = SimpleNamespace(product_idea=idea)
        opportunity = SimpleNamespace(status="review", supplier_offer_id=1, supplier_offer=offer, supplier_price=10, shipping_cost=2, other_costs=0, market_price=20, saturation_level="moderate", demand_score=0, opportunity_score=0, save=MagicMock())
        result = OpportunityDemandStudyCompletionService.run(opportunity)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["verified_count"], 1)
        self.assertEqual(len(idea.demand_signal_assessments), 1)
        self.assertEqual(idea.demand_signal_assessments[0]["source_url"], valid["source_url"])
        self.assertTrue(idea.demand_signal_assessments[0]["is_verified"])
        idea.save.assert_called_once()

    @patch("product_intelligence.services.opportunity_demand_evidence_search.OpportunityDemandEvidenceSearchService.search", return_value=[])
    def test_no_evidence_keeps_study_unresolved(self, search):
        idea = SimpleNamespace(demand_signal_assessments=[], save=MagicMock())
        opportunity = SimpleNamespace(status="review", supplier_offer_id=1, supplier_offer=SimpleNamespace(product_idea=idea))
        result = OpportunityDemandStudyCompletionService.run(opportunity)
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["reason"], "no_new_growth_evidence")
        idea.save.assert_not_called()
