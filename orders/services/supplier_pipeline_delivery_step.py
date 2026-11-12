from orders.models import SupplierOrder, OrderProcessingEvent
from orders.services.supplier_order_sandbox_runner import SupplierOrderSandboxRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelineDeliveryStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        dossiers = SupplierOrder.objects.filter(mode="sandbox", status="submitted", order__paid=True, supplier__name__iexact="cjdropshipping", supplier_status="SHIPPED").exclude(tracking_number__isnull=True).exclude(tracking_number="").select_related("order", "supplier").order_by("id")
        for dossier in dossiers:
            try:
                if OrderProcessingEvent.objects.filter(supplier_order=dossier, event_type="supplier_delivered").exists():
                    continue
                SupplierOrderSandboxRunner.run(dossier, "sync")
                dossier.refresh_from_db()
                if dossier.supplier_status != "SHIPPED" or not dossier.tracking_number:
                    continue
                SupplierOrderSandboxRunner.run(dossier, "deliver")
                dossier.refresh_from_db()
                if dossier.supplier_status == "DELIVERED":
                    result.operations_effectuees += 1
                else:
                    result.incidents.append("Dossier {} : livraison CJ non confirmee".format(dossier.id))
            except Exception as error:
                result.incidents.append("Dossier {} : livraison sandbox CJ impossible - {}".format(dossier.id, error))
        return result
