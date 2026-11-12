from decimal import Decimal
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from orders.models import (
    Order,
    OrderItem,
    OrderProcessingEvent,
    SupplierOrder,
    SupplierPreparation,
)
from orders.services.supplier_order_adapter_factory import SupplierOrderAdapterFactory
from orders.services.supplier_order_submission_service import SupplierOrderSubmissionService
from product_intelligence.models import ProductOpportunity, Supplier, SupplierOffer
from products.models import Product


class SupplierOrderSubmissionServiceTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="customer")
        self.order = Order.objects.create(
            user=user,
            first_name="John",
            last_name="Elese",
            email="john@example.com",
            phone="0102030405",
            address="9 rue du Test",
            postal_code="77700",
            city="Serris",
            country="FR",
            paid=True,
            status="paid",
        )
        self.cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )
        self.item = self._prepared_item(self.cj, "VID-1", "SKU-1")
        self.client = Mock()
        self.client.create_order_v3.return_value = {"orderId": "CJ-TEST-1"}
        self.service = SupplierOrderSubmissionService(
            SupplierOrderAdapterFactory(cj_client=self.client)
        )

    def test_submits_cj_order_with_mandatory_sandbox_flag(self):
        result = self.service.submit(self.order, sandbox=True)

        self.assertEqual(len(result), 1)
        supplier_order = result[0]
        self.assertEqual(supplier_order.status, "submitted")
        self.assertEqual(supplier_order.supplier_order_id, "CJ-TEST-1")
        self.assertEqual(supplier_order.tracking_provider, "CJPacket Ordinary I")
        payload = self.client.create_order_v3.call_args.args[0]
        self.assertEqual(payload["isSandbox"], 1)
        self.assertEqual(payload["products"][0]["vid"], "VID-1")
        self.assertEqual(payload["logisticName"], "CJPacket Ordinary I")
        self.assertEqual(payload["shopAmount"], "14.99")
        self.assertEqual(payload["iossType"], 3)
        self.assertEqual(payload["iossNumber"], "CJ-IOSS")

    def test_is_idempotent_after_success(self):
        first = self.service.submit(self.order, sandbox=True)[0]
        second = self.service.submit(self.order, sandbox=True)[0]

        self.assertEqual(first.id, second.id)
        self.client.create_order_v3.assert_called_once()

    def test_splits_one_customer_order_by_supplier(self):
        other = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            supplier_type="dropshipper",
        )
        self._prepared_item(other, "BIG-1", "BIG-SKU-1")

        with self.assertRaisesMessage(ValueError, "BigBuy"):
            self.service.submit(self.order, sandbox=True)

        self.assertEqual(SupplierOrder.objects.count(), 2)
        self.assertEqual(
            set(SupplierOrder.objects.values_list("supplier__name", flat=True)),
            {"CJdropshipping", "BigBuy"},
        )

    def test_rejects_real_mode(self):
        with self.assertRaisesMessage(ValueError, "réelle est désactivée"):
            self.service.submit(self.order, sandbox=False)
        self.client.create_order_v3.assert_not_called()

    def test_requires_frozen_shipping_method(self):
        preparation = self.item.supplier_preparation
        preparation.supplier_offer.shipping_method = ""
        preparation.supplier_offer.save(update_fields=["shipping_method"])

        with self.assertRaisesMessage(ValueError, "mode de transport"):
            self.service.submit(self.order, sandbox=True)
        self.client.create_order_v3.assert_not_called()

    def test_failed_attempt_requires_explicit_retry(self):
        self.client.create_order_v3.side_effect = [
            ValueError("CJ refused"),
            {"orderId": "CJ-TEST-RETRY"},
        ]
        with self.assertRaisesMessage(ValueError, "CJ refused"):
            self.service.submit(self.order, sandbox=True)
        with self.assertRaisesMessage(ValueError, "doit être vérifiée"):
            self.service.submit(self.order, sandbox=True)

        result = self.service.submit(
            self.order,
            sandbox=True,
            retry_failed=True,
        )[0]

        self.assertEqual(result.status, "submitted")
        self.assertEqual(result.supplier_order_id, "CJ-TEST-RETRY")

    def test_submission_records_manual_processing_event(self):
        result = self.service.submit(
            self.order,
            sandbox=True,
            source="manual",
        )

        supplier_order = result[0]
        event = OrderProcessingEvent.objects.get(
            order=self.order,
            event_type="supplier_order_submitted",
        )
        self.assertEqual(event.source, "manual")
        self.assertEqual(supplier_order.status, "submitted")

    def _prepared_item(self, supplier, vid, sku):
        product = Product.objects.create(
            name=f"Produit {vid}",
            description="Test",
            price=Decimal("14.99"),
            stock=10,
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name=product.name,
            supplier_product_id=vid,
            supplier_sku=sku,
            purchase_price=Decimal("1.14"),
            shipping_cost=Decimal("5.19"),
            shipping_days=18,
            shipping_country="FR",
            shipping_method="CJPacket Ordinary I",
            currency="USD",
            variant_features={"color": "Black", "size": "2XL"},
            supplier_verified_at=timezone.now(),
        )
        ProductOpportunity.objects.create(
            name=product.name,
            source_name=supplier.name,
            supplier_price=Decimal("0.98"),
            market_price=Decimal("14.99"),
            supplier_offer=offer,
            published_product=product,
            status="published",
        )
        item = OrderItem.objects.create(
            order=self.order,
            product=product,
            price=Decimal("14.99"),
            quantity=1,
        )
        SupplierPreparation.objects.create(
            order_item=item,
            supplier_offer=offer,
            mode="simulation",
            destination_country="FR",
            quantity=1,
            source_currency="USD",
            target_currency="EUR",
            exchange_rate=Decimal("0.857811"),
            purchase_original=Decimal("1.14"),
            shipping_original=Decimal("5.19"),
            purchase_converted=Decimal("0.98"),
            shipping_converted=Decimal("4.45"),
            base_cost=Decimal("5.43"),
            import_duty_rate=Decimal("0.04"),
            import_duty=Decimal("0.22"),
            landed_cost=Decimal("5.65"),
            rate_source="https://example.com/rate",
            supplier_verified_at=timezone.now(),
            calculated_at=timezone.now(),
        )
        return item
