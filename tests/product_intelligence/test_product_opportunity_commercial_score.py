from decimal import Decimal
from django.test import TestCase
from product_intelligence.models import ProductOpportunity


class ProductOpportunityCommercialScoreTests(TestCase):
    def create_opportunity(self):
        return ProductOpportunity.objects.create(name="Produit test commercial", source_name="Test", supplier_price=Decimal("10.00"), market_price=Decimal("30.00"), shipping_cost=Decimal("5.00"), other_costs=Decimal("3.00"), demand_score=65, competition_score=0)

    def test_missing_commercial_analysis_has_no_final_score(self):
        opportunity = self.create_opportunity()
        self.assertIsNone(opportunity.opportunity_score)

    def test_save_preserves_explicit_commercial_score(self):
        opportunity = self.create_opportunity()
        opportunity.opportunity_score = 50
        opportunity.save()
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.opportunity_score, 50)

    def test_partial_save_preserves_explicit_commercial_score(self):
        opportunity = self.create_opportunity()
        opportunity.opportunity_score = 50
        opportunity.name = "Produit modifie"
        opportunity.save(update_fields=["name", "opportunity_score"])
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.opportunity_score, 50)
