from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from dashboard.services.emma_attention_service import (
    EmmaAttentionService,
)
from product_intelligence.models import ProductOpportunity

from dashboard.services.priority_advisor import (
    PriorityAdvisor,
)

from products.models import Category

from django.core.files.uploadedfile import SimpleUploadedFile


class PriorityAdvisorTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )


class EmmaAttentionServiceTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

    def test_detects_old_unprocessed_opportunity(self):
        opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth",
            source_name="Fournisseur test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Produit de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=self.category,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        opportunity.detected_at = (
            timezone.now() - timedelta(days=8)
        )
        opportunity.save(
            update_fields=["detected_at"]
        )

        priority = PriorityAdvisor.get_priority()

        alerts = EmmaAttentionService.get_alerts(
            priority,
        )

        self.assertEqual(
            len(alerts),
            1,
        )

        self.assertEqual(
            alerts[0]["title"],
            opportunity.name,
        )

        self.assertIn(
            "plus d'une semaine",
            alerts[0]["message"],
        )

        self.assertEqual(
            alerts[0]["icon"],
            "⏳",
        )

    def test_returns_no_alert_when_priority_is_none(self):
        alerts = EmmaAttentionService.get_alerts(None)

        self.assertEqual(
            alerts,
            [],
        )



        


