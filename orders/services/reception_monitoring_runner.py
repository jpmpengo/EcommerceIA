from datetime import timedelta

from django.utils import timezone

from orders.models import Order


class ReceptionMonitoringRunner:
    @staticmethod
    def get_orders_to_notify():
        return Order.objects.filter(
            status="delivered",
            delivered_at__isnull=False,
            reception_request_sent_at__isnull=True,
            reception_request_claimed_at__isnull=True,
            customer_received_at__isnull=True,
            reception_disputed_at__isnull=True,
            reception_assumed_at__isnull=True,
        ).order_by("delivered_at", "id")

    @staticmethod
    def get_due_orders(now=None):
        now = now or timezone.now()
        return Order.objects.filter(
            status="delivered",
            delivered_at__isnull=False,
            delivered_at__lte=now - timedelta(days=7),
            reception_request_sent_at__isnull=False,
            reception_request_sent_at__lte=now,
            customer_received_at__isnull=True,
            reception_disputed_at__isnull=True,
            reception_assumed_at__isnull=True,
        ).order_by("delivered_at", "id")

    @classmethod
    def run(cls, limit=20, order_id=None):
        from orders.services.reception_confirmation_service import ReceptionConfirmationService
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limite invalide (1 a 100).")
        queryset = cls.get_due_orders()
        if order_id is not None:
            queryset = queryset.filter(id=order_id)
        dossiers = list(queryset[:limit])
        result = {"selected": len(dossiers), "assumed": 0, "skipped": 0, "failed": 0}
        for order in dossiers:
            try:
                applied = ReceptionConfirmationService.assume_reception(order.id)
            except Exception:
                result["failed"] += 1
            else:
                result["assumed" if applied else "skipped"] += 1
        return result

    @classmethod
    def run_notifications(cls, site_url, limit=20, order_id=None):
        from django.conf import settings
        from orders.services.reception_confirmation_service import ReceptionConfirmationService
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limite invalide (1 a 100).")
        result = {"selected": 0, "sent": 0, "skipped": 0, "failed": 0, "errors": []}
        if not getattr(settings, "ORDER_RECEPTION_AUTO_EMAIL_ENABLED", False):
            return result
        queryset = cls.get_orders_to_notify()
        if order_id is not None:
            queryset = queryset.filter(id=order_id)
        dossiers = list(queryset[:limit])
        result["selected"] = len(dossiers)
        for order in dossiers:
            try:
                sent = ReceptionConfirmationService.send_request(order.id, site_url)
            except Exception as error:
                result["failed"] += 1
                result["errors"].append({"order_id": order.id, "error": str(error)[:500]})
            else:
                result["sent" if sent else "skipped"] += 1
        return result
