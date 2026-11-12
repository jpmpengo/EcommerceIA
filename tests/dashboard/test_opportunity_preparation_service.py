from decimal import Decimal

from django.test import TestCase

from dashboard.services.opportunity_preparation_service import (
    OpportunityPreparationService,
)
from product_intelligence.models import ProductOpportunity
from products.models import Category


class OpportunityPreparationServiceTests(TestCase):

    def setUp(self):
        self.opportunity = ProductOpportunity.objects.create(
            name="Raw supplier title",
            source_name="Supplier",
            supplier_price=Decimal("0.98"),
            market_price=Decimal("14.99"),
            status="approved",
        )

    def test_updates_text_and_creates_category(self):
        OpportunityPreparationService.update(
            opportunity=self.opportunity,
            name="Culotte menstruelle noire 2XL",
            description=(
                "Culotte menstruelle noire réutilisable en taille 2XL, "
                "conçue pour offrir une protection confortable au quotidien."
            ),
            new_category_name="Hygiène & Bien-être",
        )

        self.opportunity.refresh_from_db()

        self.assertEqual(
            self.opportunity.name,
            "Culotte menstruelle noire 2XL",
        )
        self.assertEqual(
            self.opportunity.category.name,
            "Hygiène & Bien-être",
        )
        self.assertEqual(
            self.opportunity.category.slug,
            "hygiene-bien-etre",
        )

    def test_uses_existing_category(self):
        category = Category.objects.create(
            name="Hygiène & Bien-être",
            slug="hygiene-bien-etre",
        )

        OpportunityPreparationService.update(
            opportunity=self.opportunity,
            name="Culotte menstruelle noire 2XL",
            description=(
                "Culotte menstruelle noire réutilisable en taille 2XL, "
                "conçue pour offrir une protection confortable au quotidien."
            ),
            category_id=category.pk,
        )

        self.opportunity.refresh_from_db()
        self.assertEqual(self.opportunity.category, category)

    def test_rejects_short_description(self):
        with self.assertRaisesMessage(
            ValueError,
            "La description doit contenir au moins 50 caractères.",
        ):
            OpportunityPreparationService.update(
                opportunity=self.opportunity,
                name="Culotte menstruelle noire 2XL",
                description="Trop courte.",
                new_category_name="Hygiène & Bien-être",
            )
