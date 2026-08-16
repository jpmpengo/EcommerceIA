from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    ProductOpportunity,
)
from dashboard.services.publication_readiness_service import (
    PublicationReadinessService,
)

from products.models import Category

from django.core.files.uploadedfile import SimpleUploadedFile


class PublicationReadinessServiceTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

    def test_detects_missing_category(self):
        opportunity = ProductOpportunity.objects.create(
            name="Produit incomplet",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Produit de test",
            initial_stock=5,
            category=None,
        )

        result = PublicationReadinessService.evaluate(
            opportunity
        )

        self.assertFalse(
            result["ready"]
        )

        self.assertEqual(
            result["missing"][0]["field"],
            "category",
        )

    def test_detects_missing_description(self):
        opportunity = ProductOpportunity.objects.create(
            name="Produit sans description",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="",
            initial_stock=5,
            category=self.category,

            image=SimpleUploadedFile(
                "test.jpg",
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

        self.assertEqual(
            len(result["missing"]),
            1,
        )

        self.assertEqual(
            result["missing"][0]["field"],
            "description",
        )

        self.assertEqual(
            result["missing"][0]["label"],
            "Description",
        )

    def test_detects_description_too_short(self):
        opportunity = ProductOpportunity.objects.create(
            name="Produit test",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=80,
            competition_score=40,
            status="approved",
            description="Bon produit",
            initial_stock=5,
            category=self.category,
        )

        result = PublicationReadinessService.evaluate(
            opportunity
        )

        self.assertFalse(
            result["ready"]
        )

        self.assertEqual(
            result["missing"][0]["field"],
            "description",
        )

        self.assertEqual(
            result["missing"][0]["label"],
            "Description",
        )
    
    def test_detects_missing_image(self):
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
    
    def test_detects_missing_initial_stock(self):
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
            initial_stock=0,
            category=self.category,
            image=SimpleUploadedFile(
                "support.jpg",
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

        self.assertTrue(
            any(
                item["field"] == "initial_stock"
                for item in result["missing"]
            )
        )        

        