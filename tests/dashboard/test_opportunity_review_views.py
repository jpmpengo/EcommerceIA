from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import ProductOpportunity

from django.contrib.auth.models import Group


User = get_user_model()


class OpportunityReviewViewsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="staff",
            password="test-password",
            is_staff=True,
        )

        self.client.force_login(
            self.user
        )

        self.opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="review",
        )

    def test_staff_can_approve_opportunity_in_review(self):
        response = self.client.post(
            reverse(
                "dashboard:approve_opportunity",
                args=[
                    self.opportunity.id,
                ],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:home",
            ),
        )

        self.opportunity.refresh_from_db()

        self.assertEqual(
            self.opportunity.status,
            "approved",
        )

    def test_staff_can_reject_opportunity_in_review(self):
        response = self.client.post(
            reverse(
                "dashboard:reject_opportunity",
                args=[
                    self.opportunity.id,
                ],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:home",
            ),
        )

        self.opportunity.refresh_from_db()

        self.assertEqual(
            self.opportunity.status,
            "rejected",
        )   

    def test_home_shows_opportunity_in_review(self):
        response = self.client.get(
            reverse(
                "dashboard:home",
            )
        )

        self.assertContains(
            response,
            "Wireless Charger",
        )

    from django.contrib.auth.models import Group


    def test_emma_operator_can_approve_opportunity(self):
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

        response = self.client.post(
            reverse(
                "dashboard:approve_opportunity",
                args=[self.opportunity.id],
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard:home"),
        )

        self.opportunity.refresh_from_db()

        self.assertEqual(
            self.opportunity.status,
            "approved",
        )