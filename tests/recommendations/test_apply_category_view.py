from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import ProductOpportunity
from products.models import Category


class ApplyCategoryViewTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

        self.opportunity = ProductOpportunity.objects.create(
            name="Support ordinateur portable",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description=(
                "Support réglable pour ordinateur portable."
            ),
            initial_stock=5,
            category=None,
        )

    def test_apply_category_assigns_suggested_category(self):
        response = self.client.get(
            reverse(
                "recommendations:apply_category",
                args=[self.opportunity.pk],
            )
        )

        self.opportunity.refresh_from_db()

        self.assertEqual(
            self.opportunity.category,
            self.category,
        )

        self.assertRedirects(
            response,
            reverse(
                "recommendations:detail",
                args=[self.opportunity.pk],
            ),
        )

        