from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from orders.models import SupplierOrder
from orders.services.supplier_order_sandbox_runner import SupplierOrderSandboxRunner


class SupplierOrderMonitoringRunner:
    @staticmethod
    def get_due_orders(now=None):
        now = now or timezone.now()
        return SupplierOrder.objects.filter(
            mode="sandbox",
            status="submitted",
        ).exclude(
            supplier_status="DELIVERED",
        ).filter(
            Q(next_check_at__isnull=True) | Q(next_check_at__lte=now)
        ).select_related("supplier", "order").order_by("next_check_at", "id")

    @staticmethod
    def schedule_next_check(supplier_order, now=None):
        now = now or timezone.now()
        if supplier_order.supplier_status == "DELIVERED":
            supplier_order.next_check_at = None
        elif supplier_order.supplier_status == "SHIPPED":
            supplier_order.next_check_at = now + timedelta(hours=24)
        else:
            supplier_order.next_check_at = now + timedelta(hours=12)
        supplier_order.save(update_fields=["next_check_at"])
        return supplier_order.next_check_at

    @classmethod
    def run(cls, limit=20, order_id=None):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limite invalide (1 a 100).")
        result = {"selected": 0, "synced": 0, "failed": 0}
        queryset = cls.get_due_orders()
        if order_id is not None:
            queryset = queryset.filter(order_id=order_id)
        dossiers = list(queryset[:limit])
        result["selected"] = len(dossiers)
        for dossier in dossiers:
            try:
                SupplierOrderSandboxRunner.run(dossier, "sync")
            except (ValueError, OSError) as error:
                dossier.error_message = str(error)[:2000]
                dossier.save(update_fields=["error_message"])
                cls.schedule_next_check(dossier)
                result["failed"] += 1
            else:
                if dossier.error_message:
                    dossier.error_message = ""
                    dossier.save(update_fields=["error_message"])
                cls.schedule_next_check(dossier)
                result["synced"] += 1
        return result
