from django.utils import timezone

from orders.models import OrderProcessingEvent


class SupplierOrderLifecycleService:
    def __init__(self, adapter_factory):
        self.adapter_factory = adapter_factory

    def sync(self, supplier_order):
        adapter = self._adapter(supplier_order)
        detail = adapter.query(supplier_order.supplier_order_id)
        supplier_status = str(detail.get("orderStatus") or "")
        supplier_sub_status = str(detail.get("subStatus") or "")
        supplier_order.supplier_status = supplier_status
        supplier_order.supplier_sub_status = supplier_sub_status
        supplier_order.tracking_number = str(detail.get("trackNumber") or "")
        supplier_order.tracking_provider = str(
            detail.get("trackingProvider")
            or supplier_order.tracking_provider
            or self._shipping_method(supplier_order)
            or ""
        )
        supplier_order.tracking_url = str(detail.get("trackingUrl") or "")
        supplier_order.response_payload = detail
        supplier_order.last_synced_at = timezone.now()
        supplier_order.save(
            update_fields=[
                "supplier_status",
                "supplier_sub_status",
                "tracking_number",
                "tracking_provider",
                "tracking_url",
                "response_payload",
                "last_synced_at",
            ]
        )
        if supplier_status in {"UNPAID", "UNSHIPPED", "SHIPPED", "DELIVERED"}:
            if not OrderProcessingEvent.objects.filter(order=supplier_order.order, supplier_order=supplier_order, event_type="supplier_order_confirmed").exists():
                OrderProcessingEvent.objects.create(order=supplier_order.order, supplier_order=supplier_order, event_type="supplier_order_confirmed", source="automatic")
        self._sync_customer_order_status(
            supplier_order,
            supplier_status,
            supplier_sub_status,
        )
        return detail

    @staticmethod
    def _shipping_method(supplier_order):
        item = (
            supplier_order.items
            .select_related("supplier_preparation__supplier_offer")
            .first()
        )
        if not item or not item.supplier_preparation_id:
            return ""
        return item.supplier_preparation.supplier_offer.shipping_method

    @staticmethod
    def _sync_customer_order_status(
        supplier_order,
        supplier_status,
        supplier_sub_status,
    ):
        target = None
        if supplier_status == "DELIVERED":
            target = "delivered"
        elif supplier_status == "SHIPPED":
            target = "shipped"
        elif supplier_status == "UNSHIPPED" and supplier_sub_status == "PROCESSING":
            target = "processing"

        order = supplier_order.order
        if supplier_status == "DELIVERED" and order.delivered_at is None:
            order.delivered_at = timezone.now()
            order.save(update_fields=["delivered_at"])
        progression = {"paid": 0, "processing": 1, "shipped": 2, "delivered": 3}
        if (
            target
            and order.status in progression
            and progression[target] > progression[order.status]
        ):
            order.status = target
            order.save(update_fields=["status"])

    def simulate_pay(self, supplier_order, source="automatic"):
        self._adapter(supplier_order).simulate_pay(supplier_order.supplier_order_id)
        detail = self.sync(supplier_order)
        OrderProcessingEvent.objects.create(
            order=supplier_order.order, supplier_order=supplier_order,
            event_type="supplier_payment_completed",
            source=source,
        )
        return detail

    def confirm(self, supplier_order, source="automatic"):
        self._adapter(supplier_order).confirm(supplier_order.supplier_order_id)
        detail = self.sync(supplier_order)
        OrderProcessingEvent.objects.create(
            order=supplier_order.order, supplier_order=supplier_order,
            event_type="supplier_order_confirmed",
            source=source,
        )
        return detail

    def update_status(self, supplier_order, target_status, source="automatic"):
        self._adapter(supplier_order).update_status(
            supplier_order.supplier_order_id,
            target_status,
        )
        detail = self.sync(supplier_order)
        event_types = {
            400: "supplier_processing_started",
            500: "supplier_shipped",
            600: "supplier_delivered",
        }
        event_type = event_types.get(target_status)
        if event_type:
            OrderProcessingEvent.objects.create(
                order=supplier_order.order, supplier_order=supplier_order,
                event_type=event_type,
                source=source,
            )
        return detail

    def update_tracking(self, supplier_order, tracking_number, source="automatic"):
        self._adapter(supplier_order).update_tracking(
            supplier_order.supplier_order_id,
            tracking_number,
        )
        detail = self.sync(supplier_order)
        OrderProcessingEvent.objects.create(
            order=supplier_order.order, supplier_order=supplier_order,
            event_type="tracking_updated",
            source=source,
        )
        return detail

    def _adapter(self, supplier_order):
        if supplier_order.mode != "sandbox":
            raise ValueError("Le cycle de test est réservé aux dossiers sandbox.")
        if supplier_order.status != "submitted" or not supplier_order.supplier_order_id:
            raise ValueError("Le dossier fournisseur n'a pas été transmis.")
        return self.adapter_factory.create(supplier_order.supplier, sandbox=True)
