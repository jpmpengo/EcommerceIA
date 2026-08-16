from decimal import Decimal

from django.test import TestCase

from dashboard.services.emma_preparation_service import (
    EmmaPreparationService,
)
from product_intelligence.models import (
    ProductOpportunity,
)

from django.core.files.uploadedfile import SimpleUploadedFile

from products.models import Product

from dashboard.services.emma_preparation_service import (
    EmmaPreparationService,
)

class EmmaPreparationServiceTests(TestCase):

    def test_returns_approved_opportunity_missing_category(self):
        opportunity = ProductOpportunity.objects.create(
            name="Souris Logitech MX",
            source_name="Amazon",
            supplier_price=Decimal("35.00"),
            market_price=Decimal("79.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("2.00"),
            demand_score=85,
            competition_score=35,
            status="approved",
            description="Souris ergonomique sans fil avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=None,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        preparation = (
            EmmaPreparationService.get_items()
        )

        self.assertEqual(
            len(preparation),
            1,
        )

        self.assertEqual(
            preparation[0]["opportunity"],
            opportunity,
        )

        self.assertEqual(
            preparation[0]["title"],
            "Souris Logitech MX",
        )

        self.assertEqual(
            preparation[0]["missing"][0]["field"],
            "category",
        )

    def test_restock_opportunity_is_not_listed_as_product_to_prepare(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        items = EmmaPreparationService.get_items()

        self.assertEqual(
            items,
            [],
        )

        
        