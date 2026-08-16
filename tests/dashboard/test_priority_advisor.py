from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from dashboard.services.priority_advisor import PriorityAdvisor
from product_intelligence.models import ProductOpportunity

from datetime import timedelta

from django.utils import timezone

from products.models import Category

from django.core.files.uploadedfile import SimpleUploadedFile


class PriorityAdvisorTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

    def test_returns_first_approved_opportunity(self):
        opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth AAC",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Casque Bluetooth de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=self.category,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        priority = PriorityAdvisor.get_priority()

        self.assertEqual(
            priority["title"],
            "Publier Casque Bluetooth AAC",
        )

        self.assertEqual(
            priority["action_label"],
            "Voir la recommandation",
        )

        self.assertEqual(
            priority["action_url"],
            reverse(
                "recommendations:detail",
                args=[opportunity.pk],
            ),
        )

    def test_returns_none_when_no_priority_exists(self):
        priority = PriorityAdvisor.get_priority()

        self.assertIsNone(priority)

    def test_priority_contains_reasons(self):
        ProductOpportunity.objects.create(
            name="Casque Bluetooth AAC",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Casque Bluetooth de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=self.category,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        priority = PriorityAdvisor.get_priority()

        self.assertIn(
            "reasons",
            priority,
        )

        self.assertIsInstance(
            priority["reasons"],
            list,
        )

        self.assertGreater(
            len(priority["reasons"]),
            0,
        )

    def test_ignores_postponed_opportunity(self):
        ProductOpportunity.objects.create(
            name="Produit reporté",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Produit reporté avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=self.category,
            postponed_until=(
                timezone.now() + timedelta(days=14)
            ),
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        priority = PriorityAdvisor.get_priority()

        self.assertIsNone(priority)

    def test_ignores_approved_opportunity_without_category(self):
        opportunity = ProductOpportunity.objects.create(
            name="Produit sans catégorie",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Produit sans catégorie avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=None,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        priority = PriorityAdvisor.get_priority()

        self.assertIsNone(priority)




        