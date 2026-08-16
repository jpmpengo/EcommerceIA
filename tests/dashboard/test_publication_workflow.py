from decimal import Decimal

from django.test import TestCase

from dashboard.services.category_assignment_service import (
    CategoryAssignmentService,
)
from dashboard.services.publication_readiness_service import (
    PublicationReadinessService,
)
from product_intelligence.models import ProductOpportunity
from products.models import Category

from django.core.files.uploadedfile import SimpleUploadedFile


class PublicationWorkflowTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

    def test_opportunity_becomes_ready_after_category_assignment(self):
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
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        result = PublicationReadinessService.evaluate(
            opportunity
        )

        self.assertFalse(
            result["ready"]
        )

        CategoryAssignmentService.assign(
            opportunity,
            self.category,
        )

        opportunity.refresh_from_db()

        result = PublicationReadinessService.evaluate(
            opportunity
        )

        self.assertTrue(
            result["ready"]
        )

        self.assertEqual(
            len(result["missing"]),
            0,
        )
        
    def test_opportunity_becomes_ready_after_image_assignment(self):
        opportunity = ProductOpportunity.objects.create(
            name="Support ordinateur portable",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=80,
            competition_score=40,
            status="approved",
            description=(
                "Support réglable et pratique pour ordinateur portable, "
                "adapté au travail quotidien et au télétravail."
            ),
            initial_stock=5,
            category=self.category,
            image=None,
        )

        # Avant l'ajout de l'image
        result = PublicationReadinessService.evaluate(
            opportunity
        )

        self.assertFalse(
            result["ready"]
        )

        self.assertTrue(
            any(
                item["field"] == "image"
                for item in result["missing"]
            )
        )

        # Le commerçant ajoute une image
        opportunity.image = SimpleUploadedFile(
            "support.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        opportunity.save()

        # Emma réévalue l'opportunité
        result = PublicationReadinessService.evaluate(
            opportunity
        )

        self.assertTrue(
            result["ready"]
        )

        self.assertEqual(
            result["missing"],
            []
        )