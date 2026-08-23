from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import ProductOpportunity

from product_intelligence.services.analyzer import (
    OpportunityAnalyzer,
)


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

    def test_unknown_market_scores_do_not_add_points(
        self,
    ):
        opportunity = ProductOpportunity.objects.create(
            name="Produit sans données marché",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            shipping_cost=Decimal("0.00"),
            demand_score=0,
            competition_score=0,
        )

        score = (
            OpportunityAnalyzer
            .opportunity_score(
                opportunity
            )
        )

        self.assertEqual(
            score,
            40,
        )

    def test_margin_is_unreliable_when_shipping_cost_is_unknown(
        self,
    ):
        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit sans frais connus",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "30.00"
                ),
                shipping_cost=Decimal(
                    "0.00"
                ),
                shipping_cost_is_known=False,
                other_costs=Decimal(
                    "0.00"
                ),
            )
        )

        self.assertFalse(
            OpportunityAnalyzer
            .margin_is_reliable(
                opportunity
            )
        )

    def test_free_shipping_can_be_reliable_when_known(
        self,
    ):
        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit avec livraison gratuite",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "30.00"
                ),
                shipping_cost=Decimal(
                    "0.00"
                ),
                shipping_cost_is_known=True,
                other_costs=Decimal(
                    "0.00"
                ),
            )
        )

        self.assertTrue(
            OpportunityAnalyzer
            .margin_is_reliable(
                opportunity
            )
        )