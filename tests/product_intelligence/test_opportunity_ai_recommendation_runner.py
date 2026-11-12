from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from product_intelligence.models import ProductOpportunity, Supplier, SupplierOffer
from product_intelligence.services.opportunity_ai_recommendation_runner import OpportunityAIRecommendationRunner

class FakeEngine:
    def __init__(self):
        self.context = None
    def recommend(self, context):
        self.context = context
        return dict(decision='recommend', summary='Dossier commercial documente')

class OpportunityAIRecommendationRunnerTests(TestCase):
    def test_indeterminate_saturation_creates_competition_blocker(self):
        opportunity = ProductOpportunity.objects.create(name="Produit concurrence inconnue", source_name="Test", supplier_price=Decimal("10.00"), market_price=Decimal("30.00"), demand_score=70, competition_score=40, saturation_level="indeterminate", opportunity_score=None)
        recommendation = OpportunityAIRecommendationRunner.run(opportunity, engine=None)
        self.assertEqual(recommendation.decision, "study")
        self.assertEqual(len(recommendation.study_blockers), 1)
        self.assertEqual(recommendation.study_blockers[0]["category"], "competition")
        self.assertEqual(recommendation.model_name, "")

    def test_transmits_commercial_median_to_ai(self):
        opportunity = ProductOpportunity.objects.create(name='Produit test', source_name='Test', supplier_price=Decimal('10.00'), market_price=Decimal('80.00'), recommended_price=Decimal('40.00'), demand_score=70, competition_score=40, opportunity_score=75, saturation_level='moderate')
        engine = FakeEngine()
        summary = dict(minimum_price=Decimal('38.99'), median_price=Decimal('76.97'), commercial_median_price=Decimal('53.99'), maximum_price=Decimal('315.99'), retained_count=4, source_domain_count=4, shipping_comparables=[])
        with patch('product_intelligence.services.opportunity_ai_recommendation_runner.ComparablePriceSummaryService.summarize', return_value=summary):
            supplier = Supplier.objects.create(name='Fournisseur test', country='CN', website='https://example.com', supplier_type='dropshipper')
            offer = SupplierOffer.objects.create(supplier=supplier, product_name='Produit test', purchase_price=Decimal('10.00'), currency='EUR')
            opportunity.supplier_offer = offer
            OpportunityAIRecommendationRunner.run(opportunity, engine)
        comparables = engine.context['product']['market_comparables']
        self.assertEqual(comparables['median_price'], Decimal('76.97'))
        self.assertEqual(comparables['commercial_median_price'], Decimal('53.99'))
