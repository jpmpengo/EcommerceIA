from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from orders.models import Order
from orders.services.customer_satisfaction_service import CustomerSatisfactionService
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelineSatisfactionStep:
    @staticmethod
    def run(limit=20, order_id=None, site_url=None):
        result = SupplierPipelineResult()
        delay = timedelta(days=max(0, settings.ORDER_SATISFACTION_DELAY_DAYS))
        cutoff = timezone.now() - delay
        orders = Order.objects.filter(status='delivered', reception_disputed_at__isnull=True).filter(Q(customer_received_at__lte=cutoff) | Q(reception_assumed_at__lte=cutoff)).exclude(satisfaction__request_claimed_at__isnull=False).exclude(satisfaction__request_sent_at__isnull=False).exclude(satisfaction__responded_at__isnull=False).order_by('id')
        if order_id is not None:
            orders = orders.filter(id=order_id)
        for order in orders[:limit]:
            try:
                if CustomerSatisfactionService.send_request(order.id, site_url):
                    result.operations_effectuees += 1
            except Exception as exc:
                result.incidents.append('Commande {} : enquete satisfaction impossible - {}'.format(order.id, exc))
        return result
