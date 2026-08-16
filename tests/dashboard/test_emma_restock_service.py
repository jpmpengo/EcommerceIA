from decimal import Decimal

from django.test import TestCase

from products.models import Product
from product_intelligence.models import (
    ProductOpportunity,
    Supplier,
    SupplierOffer,
)

from dashboard.services.emma_restock_service import (
    EmmaRestockService,
)


class EmmaRestockServiceTests(TestCase):

    def test_returns_approved_restock_opportunity(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
            supplier_offer=offer,
        )

        items = EmmaRestockService.get_items()

        self.assertEqual(
            len(items),
            1,
        )

        self.assertEqual(
            items[0]["opportunity"],
            opportunity,
        )

        self.assertEqual(
            items[0]["product"],
            product,
        )

        self.assertEqual(
            items[0]["current_stock"],
            0,
        )

        self.assertEqual(
            items[0]["supplier_stock"],
            250,
        )

        self.assertEqual(
            items[0]["suggested_stock"],
            10,
        )

        