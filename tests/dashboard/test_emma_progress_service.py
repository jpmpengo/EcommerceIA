from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from dashboard.services.emma_progress_service import (
    EmmaProgressService,
)
from products.models import Category, Product

from django.core.files.uploadedfile import SimpleUploadedFile


class EmmaProgressServiceTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
        )

    def test_returns_new_product_published_since_previous_visit(
        self,
    ):
        previous_visit = (
            timezone.now() - timedelta(hours=1)
        )

        Product.objects.create(
            category=self.category,
            name="Casque Bluetooth AAC",
            description="Produit de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            price=Decimal("79.90"),
            stock=5,
            is_available=True,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        progress = EmmaProgressService.get_progress(
            previous_visit
        )

        self.assertEqual(
            len(progress),
            1,
        )

        self.assertEqual(
            progress[0]["icon"],
            "🎉",
        )

        self.assertIn(
            "publié",
            progress[0]["message"],
        )

        

