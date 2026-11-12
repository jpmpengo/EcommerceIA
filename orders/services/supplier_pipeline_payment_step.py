from django.db import IntegrityError, transaction
from orders.models import SupplierOrder, OrderProcessingEvent
from orders.services.supplier_order_sandbox_runner import SupplierOrderSandboxRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelinePaymentStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        dossiers = SupplierOrder.objects.filter(mode="sandbox", status="submitted", order__paid=True, supplier__name__iexact="cjdropshipping").select_related("supplier").order_by("id")
        for dossier in dossiers:
            if dossier.supplier_status != "UNPAID":
                continue
            if not dossier.supplier_order_id:
                result.incidents.append("Dossier {} : identifiant CJ manquant".format(dossier.id))
                continue
            if OrderProcessingEvent.objects.filter(supplier_order=dossier, event_type="supplier_payment_completed").exists():
                continue
            try:
                SupplierOrderSandboxRunner.run(dossier, "sync")
                dossier.refresh_from_db()
                if dossier.supplier_status != "UNPAID":
                    continue
                if OrderProcessingEvent.objects.filter(supplier_order=dossier, event_type="supplier_payment_completed").exists():
                    continue
                if not OrderProcessingEvent.objects.filter(supplier_order=dossier, event_type="supplier_order_confirmed").exists():
                    result.incidents.append("Dossier {} : confirmation CJ non tracee".format(dossier.id))
                    continue
                if OrderProcessingEvent.objects.filter(supplier_order=dossier, event_type="supplier_payment_attempted").exists():
                    result.incidents.append("Dossier {} : tentative de paiement precedente a verifier".format(dossier.id))
                    continue
                try:
                    with transaction.atomic():
                        OrderProcessingEvent.objects.create(order=dossier.order, supplier_order=dossier, event_type="supplier_payment_attempted", source="automatic")
                except IntegrityError:
                    result.incidents.append("Dossier {} : tentative de paiement deja reservee".format(dossier.id))
                    continue
                SupplierOrderSandboxRunner.run(dossier, "pay")
                result.operations_effectuees += 1
            except Exception as error:
                result.incidents.append("Dossier {} : paiement CJ impossible - {}".format(dossier.id, error))
        return result
