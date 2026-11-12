from orders.models import Order, SupplierOrder, SupplierPreparation
from orders.services.supplier_order_submission_runner import SupplierOrderSubmissionRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelineSubmissionStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        for order in Order.objects.filter(paid=True).order_by("id"):
            items = list(order.items.all())
            if not items:
                continue
            if any(not SupplierPreparation.objects.filter(order_item=item).exists() for item in items):
                if all(getattr(getattr(item.product, "source_opportunity", None), "supplier_offer", None) is not None for item in items):
                    result.relance_demandee = True
                    result.motifs_relance.append("Commande {} : preparation fournisseur manquante".format(order.id))
                continue
            dossiers = SupplierOrder.objects.filter(order=order, mode="sandbox")
            if dossiers.filter(status="failed").exists():
                result.incidents.append("Commande {} : dossier fournisseur en echec".format(order.id))
                continue
            if order.status != "paid":
                if not dossiers.filter(status="submitted").exists():
                    result.incidents.append("Commande {} : statut client avance sans soumission".format(order.id))
                continue
            if dossiers.exists() and not dossiers.exclude(status="submitted").exists():
                continue
            try:
                report = SupplierOrderSubmissionRunner.run_with_report(order, sandbox=True, retry_failed=False, source="automatic")
                result.operations_effectuees += len(report["supplier_orders"])
                if report["failed"]:
                    result.incidents.append("Commande {} : {} echec(s) de soumission".format(order.id, report["failed"]))
            except Exception as error:
                result.incidents.append("Commande {} : soumission impossible - {}".format(order.id, error))
        return result
