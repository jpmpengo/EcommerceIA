from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from dashboard.services.emma_changes_service import (
    EmmaChangesService,
)
from product_intelligence.models import ProductOpportunity

from django.core.files.uploadedfile import SimpleUploadedFile


class EmmaChangesServiceTests(TestCase):

    def test_returns_new_opportunity_detected_after_previous_visit(
        self,
    ):
        previous_visit = (
            timezone.now() - timedelta(hours=1)
        )

        opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth AAC",
            source_name="Fournisseur test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="detected",
            description="Casque Bluetooth de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        changes = EmmaChangesService.get_changes(
            previous_visit
        )

        self.assertEqual(
            len(changes),
            1,
        )

        self.assertIn(
            "1 nouvelle opportunité",
            changes[0]["message"],
        )

        self.assertEqual(
            changes[0]["icon"],
            "✨",
        )

        