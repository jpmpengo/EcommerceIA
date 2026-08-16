from decimal import Decimal

from django.test import TestCase

from products.models import Product
from product_intelligence.models import (
    ProductOpportunity,
)
from product_intelligence.services.restock_service import (
    RestockService,
)


class RestockServiceTests(TestCase):

    def test_restock_increases_existing_product_stock(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        result = RestockService.restock(
            opportunity=opportunity,
            quantity=10,
        )

        product.refresh_from_db()

        self.assertEqual(
            product.stock,
            10,
        )

        self.assertEqual(
            result,
            product,
        )

    def test_restock_rejects_zero_or_negative_quantity(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Restock quantity must be greater than zero.",
        ):
            RestockService.restock(
                opportunity=opportunity,
                quantity=0,
            )


    def test_restock_requires_approved_status(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="review",
            restock_product=product,
        )

        with self.assertRaisesMessage(
            ValueError,
            "This restock opportunity must be approved.",
        ):
            RestockService.restock(
                opportunity=opportunity,
                quantity=10,
            )


    def test_restock_requires_restock_product(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
        )

        with self.assertRaisesMessage(
            ValueError,
            "This opportunity is not a restock opportunity.",
        ):
            RestockService.restock(
                opportunity=opportunity,
                quantity=10,
            )

    def test_restock_marks_opportunity_as_restocked(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        RestockService.restock(
            opportunity=opportunity,
            quantity=10,
        )

        opportunity.refresh_from_db()

        self.assertEqual(
            opportunity.status,
            "restocked",
        )