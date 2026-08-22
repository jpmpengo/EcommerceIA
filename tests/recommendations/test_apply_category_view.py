from decimal import Decimal

from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import (
    ProductOpportunity,
)
from products.models import Category


class ApplyCategoryViewTests(TestCase):

    def setUp(self):
        self.emma_user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator",
                email="emma@example.com",
                password=(
                    "MotDePasse-Test-2026!"
                ),
            )
        )

        emma_group = Group.objects.create(
            name="Emma Operators"
        )

        self.emma_user.groups.add(
            emma_group
        )

        self.client.login(
            username="emma_operator",
            password=(
                "MotDePasse-Test-2026!"
            ),
        )

        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

        self.opportunity = (
            ProductOpportunity.objects.create(
                name=(
                    "Support ordinateur portable"
                ),
                source_name="Test",
                supplier_price=Decimal(
                    "20.00"
                ),
                market_price=Decimal(
                    "60.00"
                ),
                shipping_cost=Decimal(
                    "5.00"
                ),
                other_costs=Decimal(
                    "5.00"
                ),
                demand_score=90,
                competition_score=40,
                status="approved",
                description=(
                    "Support réglable pour "
                    "ordinateur portable."
                ),
                initial_stock=5,
                category=None,
            )
        )

    def test_apply_category_assigns_suggested_category(
        self,
    ):
        response = self.client.post(
            reverse(
                "recommendations:apply_category",
                args=[
                    self.opportunity.pk,
                ],
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
                args=[
                    self.opportunity.pk,
                ],
            ),
        )
