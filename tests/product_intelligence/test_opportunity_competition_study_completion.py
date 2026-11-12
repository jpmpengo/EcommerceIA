from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase
from product_intelligence.models import ProductIdea, ProductOpportunity, Supplier, SupplierOffer
from product_intelligence.services.opportunity_competition_study_completion import OpportunityCompetitionStudyCompletionService


class OpportunityCompetitionStudyCompletionTests(TestCase):
    def test_updates_saturation_without_changing_economic_data(self):
        idea = ProductIdea.objects.create(name="Produit test", customer_problem="Probleme", target_customer="Client", reason_to_study="Raison", countries=["FR"])
        supplier = Supplier.objects.create(name="Fournisseur test")
        offer = SupplierOffer.objects.create(product_idea=idea, supplier=supplier, product_name="Produit test", purchase_price=Decimal("10.00"))
        opportunity = ProductOpportunity.objects.create(name="Produit test", source_name="Test", supplier_offer=offer, supplier_price=Decimal("10.00"), market_price=Decimal("30.00"), shipping_cost=Decimal("5.00"), other_costs=Decimal("3.00"), demand_score=65, competition_score=0, status="review")
        service = Mock()
        service.search.return_value = {"level": "moderate", "justification": "Preuves concurrentielles verifiees", "sources": ["https://example.org/produit"]}
        with patch("product_intelligence.services.product_idea_manual_analysis.ProductIdeaManualAnalysisService.build_saturation_service", return_value=service):
            result = OpportunityCompetitionStudyCompletionService.run(opportunity)
        opportunity.refresh_from_db()
        self.assertEqual(result["status"], "updated")
        self.assertEqual(opportunity.saturation_level, "moderate")
        self.assertEqual(opportunity.opportunity_score, 78)
        self.assertEqual(opportunity.supplier_price, Decimal("10.00"))
        self.assertEqual(opportunity.shipping_cost, Decimal("5.00"))
        self.assertEqual(opportunity.market_price, Decimal("30.00"))
