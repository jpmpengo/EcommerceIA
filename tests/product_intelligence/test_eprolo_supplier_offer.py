from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import Supplier
from product_intelligence.services.eprolo_supplier_offer import (
    EproloSupplierOfferService,
)


class EproloSupplierOfferServiceTests(TestCase):

    def test_persists_variant_and_parent_identifiers(self):
        supplier = Supplier.objects.create(
            name="EPROLO",
            country="CN",
            supplier_type="dropshipper",
        )
        offer = EproloSupplierOfferService().create_offer_from_variant(
            supplier=supplier,
            product={
                "id": "32552962",
                "title": "Hoodie",
                "imagefirst": "https://example.com/image.jpg",
            },
            variant={
                "id": "729665812",
                "title": "Royal Blue-XXXL",
                "sku": "D60E4",
                "cost": 3.94,
                "inventory_quantity": 9999,
            },
        )

        self.assertEqual(offer.purchase_price, Decimal("3.94"))
        self.assertEqual(
            offer.product_name,
            "Hoodie - Royal Blue-XXXL",
        )
        self.assertEqual(offer.currency, "USD")
        self.assertEqual(offer.supplier_product_id, "729665812")
        self.assertEqual(offer.supplier_parent_product_id, "32552962")
        self.assertEqual(offer.supplier_sku, "D60E4")
        self.assertTrue(offer.is_available)

    def test_persists_supplier_search_keyword(self):
        supplier = Supplier.objects.create(
            name="EPROLO",
            country="CN",
            supplier_type="dropshipper",
        )
        offer = EproloSupplierOfferService().create_offer_from_variant(
            supplier=supplier,
            product={
                "id": "32552962",
                "title": "Bike Light",
                "imagefirst": "https://example.com/image.jpg",
            },
            variant={
                "id": "729665812",
                "title": "Black",
                "sku": "D60E4",
                "cost": 3.94,
                "inventory_quantity": 9999,
            },
            supplier_search_keyword="USB rechargeable bike light",
        )
        self.assertEqual(
            offer.supplier_search_keyword,
            "USB rechargeable bike light",
        )
