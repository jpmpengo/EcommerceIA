from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.models import Supplier, SupplierOffer
from product_intelligence.services.cj_supplier_offer_verification import CJSupplierOfferVerificationService


class CJSupplierOfferVerificationServiceTests(TestCase):

    def test_marks_offer_unavailable_when_country_stock_disappears(self):
        supplier = Supplier.objects.create(name="CJdropshipping")
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Produit CJ sans stock DE",
            purchase_price="9.00",
            currency="USD",
            stock=12,
            stock_country="DE",
            is_available=True,
            supplier_product_id="VID-2",
        )
        client = Mock()
        client.get_variant_by_id.return_value = {
            "vid": "VID-2",
            "pid": "PID-2",
            "variantSku": "SKU-2",
        }
        client.get_variant_stock.return_value = None

        result = CJSupplierOfferVerificationService(client).verify(offer)

        offer.refresh_from_db()
        self.assertFalse(offer.is_available)
        self.assertEqual(offer.stock, 12)
        self.assertEqual(result["status"], "unavailable")
        client.get_variant_stock.assert_called_once_with(
            variant_id="VID-2",
            country_code="DE",
        )

    def test_marks_offer_available_and_refreshes_country_stock(self):
        supplier = Supplier.objects.create(name="CJdropshipping")
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Produit CJ valide",
            purchase_price="9.00",
            currency="USD",
            stock=12,
            stock_country="DE",
            is_available=None,
            supplier_product_id="VID-1",
        )
        client = Mock()
        client.get_variant_by_id.return_value = {
            "vid": "VID-1",
            "pid": "PID-1",
            "variantSku": "SKU-1",
        }
        client.get_variant_stock.return_value = 45

        result = CJSupplierOfferVerificationService(client).verify(offer)

        offer.refresh_from_db()
        self.assertTrue(offer.is_available)
        self.assertEqual(offer.stock, 45)
        self.assertEqual(result["status"], "available")
        client.get_variant_stock.assert_called_once_with(
            variant_id="VID-1",
            country_code="DE",
        )

    def test_marks_offer_unavailable_when_variant_no_longer_exists(self):
        supplier = Supplier.objects.create(name="CJdropshipping")
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Produit CJ historique",
            purchase_price="5.82",
            currency="USD",
            stock=18,
            stock_country="DE",
            supplier_product_id="2071556015536246786",
        )
        client = Mock()
        client.get_variant_by_id.return_value = None

        result = CJSupplierOfferVerificationService(client).verify(offer)

        offer.refresh_from_db()
        self.assertFalse(offer.is_available)
        self.assertEqual(offer.stock, 18)
        self.assertEqual(result["status"], "unavailable")
        client.get_variant_by_id.assert_called_once_with(
            "2071556015536246786"
        )

