from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import ProductOpportunity


class OpportunityAnalyzerTests(TestCase):

    def setUp(self):

        self.opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth",
            source_name="Test",
            supplier_price=Decimal("20"),
            market_price=Decimal("60"),
            shipping_cost=Decimal("5"),
            other_costs=Decimal("5"),
            demand_score=90,
            competition_score=40,
        )

    def test_total_cost(self):

        self.assertEqual(
            self.opportunity.get_total_cost(),
            Decimal("30"),
        )

    def test_estimated_margin(self):

        self.assertEqual(
            self.opportunity.get_estimated_margin(),
            Decimal("30"),
        )