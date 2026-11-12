from orders.models import SupplierOrder
from orders.services.supplier_order_sandbox_runner import SupplierOrderSandboxRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelineLogisticsStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        dossiers = SupplierOrder.objects.filter(mode="sandbox", status="submitted", order__paid=True, supplier__name__iexact="cjdropshipping", supplier_status__in=["UNSHIPPED", "SHIPPED"]).select_related("order", "supplier").order_by("id")
        for dossier in dossiers:
            if not dossier.supplier_order_id:
                result.incidents.append("Dossier {} : identifiant CJ manquant".format(dossier.id))
                continue
            try:
                before = (dossier.supplier_status, dossier.supplier_sub_status, dossier.tracking_number, dossier.tracking_provider, dossier.tracking_url)
                SupplierOrderSandboxRunner.run(dossier, "sync")
                dossier.refresh_from_db()
                if dossier.supplier_status == "SHIPPED" and not dossier.tracking_number:
                    tracking_number = "SANDBOX-ECOMMERCEIA-{}-{}".format(dossier.order_id, dossier.id)
                    SupplierOrderSandboxRunner.run(dossier, "tracking", tracking_number=tracking_number)
                    dossier.refresh_from_db()
                after = (dossier.supplier_status, dossier.supplier_sub_status, dossier.tracking_number, dossier.tracking_provider, dossier.tracking_url)
                if after != before:
                    result.operations_effectuees += 1
            except Exception as error:
                result.incidents.append("Dossier {} : suivi logistique CJ impossible - {}".format(dossier.id, error))
        return result
