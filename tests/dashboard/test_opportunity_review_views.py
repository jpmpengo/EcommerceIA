from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import (
    ProductOpportunity,
    Supplier,
    SupplierOffer,
)

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
            demand_score=80,
            competition_score=50,
            status="review",
            market_collection_batch_id=uuid4(),
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


    def test_briefing_does_not_show_functions_from_other_spaces(self):
        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertNotContains(response, "Idées de produits")
        self.assertNotContains(response, "Produits dans la boutique")
        self.assertNotContains(response, "Commandes enregistrées")

    def test_home_shows_supplier_stock_and_country(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            stock=6,
            stock_country="FR",
        )

        self.opportunity.supplier_offer = offer
        self.opportunity.save(
            update_fields=["supplier_offer"]
        )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertContains(
            response,
            "Stock fournisseur : 6",
        )
        self.assertContains(
            response,
            "Entrepôt : FR",
        )

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