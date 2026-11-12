from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal

from product_intelligence.models import (
    ProductOpportunity,
)

User = get_user_model()


class DashboardAccessTests(TestCase):

    def test_emma_operator_can_access_dashboard_without_staff_status(self):
        group = Group.objects.create(
            name="Emma Operators",
        )

        user = User.objects.create_user(
            username="emma_operator",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        user.groups.add(group)

        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_staff_user_can_access_dashboard(self):
        user = User.objects.create_user(
            username="admin_test",
            password="test-password",
            is_staff=True,
            is_superuser=False,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )


    def test_regular_customer_is_redirected_to_product_list(self):
        user = User.objects.create_user(
            username="customer",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertRedirects(
            response,
            reverse("products:product_list"),
        )

    def test_emma_operator_can_reject_opportunity_without_staff_status(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators",
        )

        user = User.objects.create_user(
            username="emma_operator",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        user.groups.add(
            group
        )

        self.client.force_login(
            user
        )

        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit à rejeter",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "25.00"
                ),
                status="review",
            )
        )

        response = self.client.post(
            reverse(
                "dashboard:reject_opportunity",
                args=[
                    opportunity.id,
                ],
            )
        )

        opportunity.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "dashboard:home"
            ),
        )

        self.assertEqual(
            opportunity.status,
            "rejected",
        )

    def test_emma_operator_sees_pilotage_link_in_navigation(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators",
        )

        user = User.objects.create_user(
            username="emma_operator",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        user.groups.add(
            group
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "products:product_list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            reverse(
                "dashboard:home"
            ),
        )

        self.assertContains(
            response,
            "Briefing",
        )

        self.assertContains(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

        self.assertContains(
            response,
            "Pilotage",
        )

    def test_emma_operator_sees_operator_navigation(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators",
        )

        user = User.objects.create_user(
            username="emma_operator",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        user.groups.add(group)

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:home"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Briefing",
        )

        self.assertContains(
            response,
            "Pilotage",
        )

        self.assertContains(
            response,
            "Recommandations",
        )

        self.assertContains(
            response,
            "Boutique",
        )

        self.assertContains(
            response,
            reverse("orders:operator_order_list"),
        )

        self.assertContains(
            response,
            "Gestion des commandes",
        )

        self.assertNotContains(
            response,
            "Mes commandes",
        )

        self.assertNotContains(
            response,
            "Panier",
        )
