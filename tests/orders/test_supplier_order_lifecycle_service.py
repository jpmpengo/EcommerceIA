from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from orders.models import Order, OrderProcessingEvent, SupplierOrder
from orders.services.supplier_order_lifecycle_service import SupplierOrderLifecycleService
from product_intelligence.models import Supplier


class SupplierOrderLifecycleServiceTests(TestCase):
    def setUp(self):
        order = Order.objects.create(
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
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )
        self.supplier_order = SupplierOrder.objects.create(
            order=order,
            supplier=supplier,
            mode="sandbox",
            status="submitted",
            idempotency_key="TEST-1",
            supplier_order_id="SD-1",
            submitted_at=timezone.now(),
            tracking_provider="CJPacket Ordinary I",
        )
        self.adapter = Mock()
        self.adapter.query.return_value = {
            "orderStatus": "UNSHIPPED",
            "subStatus": "PENDING",
            "trackNumber": "SBX-TRACK-1",
            "trackingProvider": "Sandbox",
            "trackingUrl": "https://example.com/SBX-TRACK-1",
            "isSandbox": True,
        }
        factory = Mock()
        factory.create.return_value = self.adapter
        self.service = SupplierOrderLifecycleService(factory)

    def test_sync_persists_supplier_status_and_tracking(self):
        self.service.sync(self.supplier_order)
        self.supplier_order.refresh_from_db()

        self.assertEqual(self.supplier_order.supplier_status, "UNSHIPPED")
        self.assertEqual(self.supplier_order.supplier_sub_status, "PENDING")
        self.assertEqual(self.supplier_order.tracking_number, "SBX-TRACK-1")
        self.assertEqual(self.supplier_order.tracking_provider, "Sandbox")
        self.assertIsNotNone(self.supplier_order.last_synced_at)

    def test_keeps_selected_shipping_method_when_cj_omits_provider(self):
        self.adapter.query.return_value["trackingProvider"] = None

        self.service.sync(self.supplier_order)
        self.supplier_order.refresh_from_db()

        self.assertEqual(
            self.supplier_order.tracking_provider,
            "CJPacket Ordinary I",
        )

    def test_sync_advances_customer_status_without_downgrade(self):
        transitions = [
            ("UNSHIPPED", "PROCESSING", "processing"),
            ("SHIPPED", None, "shipped"),
            ("DELIVERED", None, "delivered"),
        ]
        for supplier_status, sub_status, expected in transitions:
            self.adapter.query.return_value.update(
                orderStatus=supplier_status,
                subStatus=sub_status,
            )
            self.service.sync(self.supplier_order)
            self.supplier_order.order.refresh_from_db()
            self.assertEqual(self.supplier_order.order.status, expected)

        self.adapter.query.return_value.update(
            orderStatus="UNSHIPPED",
            subStatus="PROCESSING",
        )
        self.service.sync(self.supplier_order)
        self.supplier_order.order.refresh_from_db()
        self.assertEqual(self.supplier_order.order.status, "delivered")

    def test_each_action_is_followed_by_sync(self):
        self.service.confirm(self.supplier_order)
        self.adapter.confirm.assert_called_once_with("SD-1")

        self.service.simulate_pay(self.supplier_order)
        self.adapter.simulate_pay.assert_called_once_with("SD-1")

        self.service.update_status(self.supplier_order, 400)
        self.adapter.update_status.assert_called_once_with("SD-1", 400)

        self.service.update_tracking(self.supplier_order, "SBX-1")
        self.adapter.update_tracking.assert_called_once_with("SD-1", "SBX-1")
        self.assertEqual(self.adapter.query.call_count, 4)

    def test_refuses_non_sandbox_order(self):
        self.supplier_order.mode = "production"
        with self.assertRaisesMessage(ValueError, "réservé"):
            self.service.sync(self.supplier_order)


class SupplierOrderLifecycleEventTests(SupplierOrderLifecycleServiceTests):
    def test_simulate_pay_records_manual_processing_event(self):
        self.service.simulate_pay(self.supplier_order, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="supplier_payment_completed",
        )
        self.assertEqual(event.source, "manual")


class SupplierOrderLifecycleEventTests(SupplierOrderLifecycleServiceTests):
    def test_simulate_pay_records_manual_processing_event(self):
        self.service.simulate_pay(self.supplier_order, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="supplier_payment_completed",
        )
        self.assertEqual(event.source, "manual")

    def test_confirm_records_manual_processing_event(self):
        self.service.confirm(self.supplier_order, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="supplier_order_confirmed",
        )
        self.assertEqual(event.source, "manual")

    def test_processing_status_records_manual_processing_event(self):
        self.service.update_status(self.supplier_order, 400, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="supplier_processing_started",
        )
        self.assertEqual(event.source, "manual")

    def test_shipped_status_records_manual_processing_event(self):
        self.service.update_status(self.supplier_order, 500, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="supplier_shipped",
        )
        self.assertEqual(event.source, "manual")

    def test_tracking_update_records_manual_processing_event(self):
        self.service.update_tracking(self.supplier_order, "SANDBOX-TRACK-TEST", source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="tracking_updated",
        )
        self.assertEqual(event.source, "manual")

    def test_delivered_status_records_manual_processing_event(self):
        self.adapter.query.return_value.update(
            orderStatus="DELIVERED",
            subStatus=None,
        )
        self.service.update_status(self.supplier_order, 600, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.supplier_order.order,
            event_type="supplier_delivered",
        )
        self.assertEqual(event.source, "manual")
        self.supplier_order.order.refresh_from_db()
        self.assertEqual(self.supplier_order.order.status, "delivered")
