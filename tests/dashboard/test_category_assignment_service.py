from decimal import Decimal

from django.test import TestCase

from dashboard.services.category_assignment_service import (
    CategoryAssignmentService,
)
from product_intelligence.models import ProductOpportunity
from products.models import Category


class CategoryAssignmentServiceTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

    def test_assign_category_to_opportunity(self):
        opportunity = ProductOpportunity.objects.create(
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
                "Support réglable pour ordinateur portable avec une description suffisamment détaillée "
                "pour permettre sa publication dans la boutique."
            ),
            initial_stock=5,
            category=None,
        )

        CategoryAssignmentService.assign(
            opportunity,
            self.category,
        )

        opportunity.refresh_from_db()

        self.assertEqual(
            opportunity.category,
            self.category,
        )

        