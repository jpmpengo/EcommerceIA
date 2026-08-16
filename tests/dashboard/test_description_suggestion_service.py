from decimal import Decimal

from django.test import TestCase

from dashboard.services.description_suggestion_service import (
    DescriptionSuggestionService,
)
from product_intelligence.models import ProductOpportunity


class DescriptionSuggestionServiceTests(TestCase):

    def test_suggests_description_for_opportunity(self):
        opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth ANC",
            source_name="Test",
            supplier_price=Decimal("30.00"),
            market_price=Decimal("79.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("2.00"),
            demand_score=85,
            competition_score=35,
            status="approved",
            description="Bon produit.",
            initial_stock=5,
        )

        suggestion = DescriptionSuggestionService.suggest(
            opportunity
        )

        self.assertIsNotNone(
            suggestion
        )

        self.assertGreaterEqual(
            len(suggestion),
            50,
        )

        self.assertIn(
            opportunity.name,
            suggestion,
        )
  
    def test_suggestion_is_customer_facing(self):
        opportunity = ProductOpportunity.objects.create(
            name="Support ordinateur portable",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=80,
            competition_score=40,
            status="approved",
            description="Support pratique pour ordinateur portable.",
            initial_stock=5,
        )

        suggestion = DescriptionSuggestionService.suggest(
            opportunity
        )

        self.assertNotIn(
            "potentiel commercial",
            suggestion.lower(),
        )

        self.assertNotIn(
            "positionnement sur le marché",
            suggestion.lower(),
        )

        self.assertNotIn(
            "cette fiche mérite",
            suggestion.lower(),
        )

        self.assertIn(
            "Support ordinateur portable",
            suggestion,
        )