from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import ProductOpportunity
from products.models import Category


User = get_user_model()


class RecommendationDetailStatusTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="emma_status_test",
            password="MotDePasse-Test-2026!",
        )
        emma_group = Group.objects.create(
            name="Emma Operators",
        )
        self.user.groups.add(emma_group)
        self.client.login(
            username="emma_status_test",
            password="MotDePasse-Test-2026!",
        )

    def test_technical_readiness_does_not_show_ready_when_market_analysis_is_incomplete(self):
        category = Category.objects.create(
            name="Rangement",
            slug="rangement",
        )

        opportunity = ProductOpportunity.objects.create(
            name="Produit techniquement prêt",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("0.00"),
            demand_score=0,
            competition_score=0,
            status="approved",
            category=category,
            description="Description commerciale suffisamment détaillée pour permettre la publication du produit dans la boutique.",
            image="product_opportunities/test.jpg",
            initial_stock=5,
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analyse à compléter")
        self.assertNotContains(response, "Prête à publier")

    def test_complete_analysis_and_technical_readiness_show_ready_to_publish(self):
        category = Category.objects.create(
            name="Organisation",
            slug="organisation",
        )

        opportunity = ProductOpportunity.objects.create(
            name="Produit prêt commercialement",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("0.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            category=category,
            description="Description commerciale suffisamment détaillée pour permettre la publication du produit dans la boutique.",
            image="product_opportunities/test-ready.jpg",
            initial_stock=5,
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prête à publier")
        self.assertNotContains(response, "Analyse à compléter")
