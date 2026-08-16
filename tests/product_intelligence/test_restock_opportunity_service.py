from decimal import Decimal

from django.test import TestCase

from products.models import Product
from product_intelligence.models import (
    ProductOpportunity,
    Supplier,
    SupplierOffer,
)

from product_intelligence.services.restock_opportunity import (
    RestockOpportunityService,
)


class RestockOpportunityServiceTests(TestCase):

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        self.product = Product.objects.create(
            name="Wireless Charger",
            description="Wireless Charger",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        self.old_offer = SupplierOffer.objects.create(
            supplier=self.supplier,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=100,
        )

        self.old_opportunity = (
            ProductOpportunity.objects.create(
                name="Wireless Charger",
                source_name="CJdropshipping",
                supplier_price=Decimal("4.53"),
                market_price=Decimal("27.90"),
                supplier_offer=self.old_offer,
                status="published",
                published_product=self.product,
            )
        )

    def test_finds_out_of_stock_published_product_for_same_supplier_product(
        self,
    ):
        new_offer = SupplierOffer.objects.create(
            supplier=self.supplier,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.75"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        product = RestockOpportunityService.find_product(
            new_offer
        )

        self.assertEqual(
            product,
            self.product,
        )

    def test_does_not_find_product_when_published_product_still_has_stock(
        self,
    ):
        self.product.stock = 5
        self.product.save(
            update_fields=["stock"]
        )

        new_offer = SupplierOffer.objects.create(
            supplier=self.supplier,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.75"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        product = RestockOpportunityService.find_product(
            new_offer
        )

        self.assertIsNone(
            product
        )

    def test_does_not_find_product_after_it_has_been_restocked(
        self,
    ):
        self.product.stock = 10
        self.product.save(
            update_fields=["stock"]
        )

        new_offer = SupplierOffer.objects.create(
            supplier=self.supplier,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.75"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        product = RestockOpportunityService.find_product(
            new_offer
        )

        self.assertIsNone(
            product
        )

    