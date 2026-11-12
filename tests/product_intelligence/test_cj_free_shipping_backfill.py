from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.models import Supplier, SupplierOffer
from product_intelligence.services.cj_free_shipping_backfill import CJFreeShippingBackfillService


class CJFreeShippingBackfillServiceTests(TestCase):

    def test_uses_parent_product_id_and_persists_explicit_free_shipping(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-1", supplier_parent_product_id="PID-1", product_name="Test", purchase_price="10.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_product_detail.return_value = {"id": "PID-1", "addMarkStatus": 1}
        client.normalize_product.return_value = {"external_id": "PID-1", "name": "Test", "currency": "USD", "free_shipping": True}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([offer])

        offer.refresh_from_db()
        client.get_product_detail.assert_called_once_with(product_id="PID-1")
        self.assertIs(offer.free_shipping, True)
        self.assertEqual(result, {"examined": 1, "updated": 1, "unchanged": 0, "unresolved": 0})

    def test_resolves_parent_product_id_from_variant_before_backfill(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-2", supplier_parent_product_id="", product_name="Test 2", purchase_price="12.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_variant_by_id.return_value = {"vid": "VID-2", "pid": "PID-2"}
        client.get_product_detail.return_value = {"id": "PID-2", "addMarkStatus": 0}
        client.normalize_product.return_value = {"external_id": "PID-2", "name": "Test 2", "currency": "USD", "free_shipping": False}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([offer])

        offer.refresh_from_db()
        client.get_variant_by_id.assert_called_once_with("VID-2")
        client.get_product_detail.assert_called_once_with(product_id="PID-2")
        self.assertIs(offer.free_shipping, False)
        self.assertEqual(result, {"examined": 1, "updated": 1, "unchanged": 0, "unresolved": 0})

    def test_leaves_unknown_when_product_has_no_explicit_free_shipping_flag(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-3", supplier_parent_product_id="PID-3", product_name="Test 3", purchase_price="15.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_product_detail.return_value = {"id": "PID-3"}
        client.normalize_product.return_value = {"external_id": "PID-3", "name": "Test 3", "currency": "USD"}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([offer])

        offer.refresh_from_db()
        self.assertIsNone(offer.free_shipping)
        self.assertEqual(result, {"examined": 1, "updated": 0, "unchanged": 0, "unresolved": 1})

    def test_reuses_product_detail_for_variants_with_same_parent(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        first = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-A", product_name="A", purchase_price="10.00", currency="USD", free_shipping=None)
        second = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-B", product_name="B", purchase_price="11.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_variant_by_id.side_effect = [
            {"vid": "VID-A", "pid": "PID-SAME"},
            {"vid": "VID-B", "pid": "PID-SAME"},
        ]
        client.get_product_detail.return_value = {"id": "PID-SAME", "addMarkStatus": 0}
        client.normalize_product.return_value = {"external_id": "PID-SAME", "name": "Test", "currency": "USD", "free_shipping": False}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([first, second])

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertIs(first.free_shipping, False)
        self.assertIs(second.free_shipping, False)
        self.assertEqual(client.get_product_detail.call_count, 1)
        self.assertEqual(result, {"examined": 2, "updated": 2, "unchanged": 0, "unresolved": 0})

    def test_does_not_cache_missing_product_detail(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        first = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-X", product_name="X", purchase_price="10.00", currency="USD", free_shipping=None)
        second = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-Y", product_name="Y", purchase_price="11.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_variant_by_id.side_effect = [
            {"vid": "VID-X", "pid": "PID-SAME"},
            {"vid": "VID-Y", "pid": "PID-SAME"},
        ]
        client.get_product_detail.side_effect = [
            None,
            None,
            {"id": "PID-SAME", "addMarkStatus": 0},
        ]
        client.normalize_product.return_value = {"external_id": "PID-SAME", "name": "Test", "currency": "USD", "free_shipping": False}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([first, second])

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertIsNone(first.free_shipping)
        self.assertIs(second.free_shipping, False)
        self.assertEqual(client.get_product_detail.call_count, 3)
        self.assertEqual(result, {"examined": 2, "updated": 1, "unchanged": 0, "unresolved": 1})

    def test_retries_product_detail_once_before_marking_unresolved(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-R", supplier_parent_product_id="PID-R", product_name="Retry", purchase_price="10.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_product_detail.side_effect = [
            None,
            {"id": "PID-R", "addMarkStatus": 1},
        ]
        client.normalize_product.return_value = {"external_id": "PID-R", "name": "Retry", "currency": "USD", "free_shipping": True}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([offer])

        offer.refresh_from_db()
        self.assertIs(offer.free_shipping, True)
        self.assertEqual(client.get_product_detail.call_count, 2)
        self.assertEqual(result, {"examined": 1, "updated": 1, "unchanged": 0, "unresolved": 0})

    def test_retries_variant_lookup_once_before_marking_unresolved(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, supplier_product_id="VID-VR", product_name="Variant retry", purchase_price="10.00", currency="USD", free_shipping=None)

        client = Mock()
        client.get_variant_by_id.side_effect = [
            None,
            {"vid": "VID-VR", "pid": "PID-VR"},
        ]
        client.get_product_detail.return_value = {"id": "PID-VR", "addMarkStatus": 0}
        client.normalize_product.return_value = {"external_id": "PID-VR", "name": "Variant retry", "currency": "USD", "free_shipping": False}

        service = CJFreeShippingBackfillService(client=client)
        result = service.run([offer])

        offer.refresh_from_db()
        self.assertIs(offer.free_shipping, False)
        self.assertEqual(client.get_variant_by_id.call_count, 2)
        self.assertEqual(result, {"examined": 1, "updated": 1, "unchanged": 0, "unresolved": 0})
