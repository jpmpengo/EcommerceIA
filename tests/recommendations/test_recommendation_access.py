from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
from decimal import Decimal

from product_intelligence.models import (
    ProductOpportunity,
)


User = get_user_model()


class RecommendationAccessTests(TestCase):


    def setUp(self):
        self.customer = (
            User.objects.create_user(
                username="ordinary_customer",
                email="customer@example.com",
                password=(
                    "MotDePasse-Test-2026!"
                ),
            )
        )

        self.client.login(
            username="ordinary_customer",
            password=(
                "MotDePasse-Test-2026!"
            ),
        )

    def test_ordinary_customer_cannot_access_recommendation_list(
        self,
    ):
        response = self.client.get(
            reverse(
                "recommendations:list"
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "products:product_list"
            ),
        )

    def test_emma_operator_can_access_recommendation_list(
        self,
    ):
        emma_group = Group.objects.create(
            name="Emma Operators"
        )

        self.customer.groups.add(
            emma_group
        )

        response = self.client.get(
            reverse(
                "recommendations:list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_ordinary_customer_cannot_access_recommendation_detail(
        self,
    ):
        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit réservé à Emma",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "25.00"
                ),
                status="approved",
            )
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[
                    opportunity.id,
                ],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "products:product_list"
            ),
        )

    def test_ordinary_customer_cannot_reject_recommendation(
        self,
    ):
        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit réservé à Emma",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "25.00"
                ),
                status="approved",
            )
        )

        response = self.client.post(
            reverse(
                "recommendations:reject",
                args=[
                    opportunity.id,
                ],
            )
        )

        opportunity.refresh_from_db()

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            reverse(
                "products:product_list"
            ),
        )

        self.assertEqual(
            opportunity.status,
            "approved",
        )

    def test_ordinary_customer_cannot_execute_recommendation_actions(
        self,
    ):
        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit réservé à Emma",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "25.00"
                ),
                status="approved",
            )
        )

        action_names = [
            "publish",
            "postpone",
            "apply_category",
            "apply_description",
            "apply_image",
            "apply_supplier_image",
            "apply_stock",
            "restock",
        ]

        for action_name in action_names:
            with self.subTest(
                action=action_name
            ):
                response = self.client.post(
                    reverse(
                        (
                            "recommendations:"
                            f"{action_name}"
                        ),
                        args=[
                            opportunity.id,
                        ],
                    ),
                    {
                        "quantity": 10,
                    },
                )

                self.assertEqual(
                    response.status_code,
                    302,
                )

                self.assertEqual(
                    response["Location"],
                    reverse(
                        "products:product_list"
                    ),
                )

    def test_get_request_cannot_reject_recommendation(
        self,
    ):
        emma_group = Group.objects.create(
            name="Emma Operators"
        )

        self.customer.groups.add(
            emma_group
        )

        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit à conserver",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "25.00"
                ),
                status="approved",
            )
        )

        response = self.client.get(
            reverse(
                "recommendations:reject",
                args=[
                    opportunity.id,
                ],
            )
        )

        opportunity.refresh_from_db()

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertEqual(
            opportunity.status,
            "approved",
        )

    def test_get_requests_cannot_execute_recommendation_actions(
        self,
    ):
        emma_group = Group.objects.create(
            name="Emma Operators"
        )

        self.customer.groups.add(
            emma_group
        )

        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit à conserver",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "25.00"
                ),
                status="approved",
            )
        )

        action_names = [
            "publish",
            "postpone",
            "reject",
            "apply_category",
            "apply_description",
            "apply_image",
            "apply_supplier_image",
            "apply_stock",
            "restock",
        ]

        for action_name in action_names:
            with self.subTest(
                action=action_name
            ):
                response = self.client.get(
                    reverse(
                        (
                            "recommendations:"
                            f"{action_name}"
                        ),
                        args=[
                            opportunity.id,
                        ],
                    )
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )