from orders.models import Order, SupplierPreparation, SupplierOrder, OrderProcessingEvent
from orders.services.supplier_preparation_runner import SupplierPreparationRunner
from orders.services.supplier_order_submission_runner import SupplierOrderSubmissionRunner
from orders.services.supplier_order_monitoring_runner import SupplierOrderMonitoringRunner
from orders.services.supplier_order_lifecycle_runner import SupplierOrderLifecycleRunner


class PaidOrderPipelineRunner:
    @staticmethod
    def get_orders():
        return Order.objects.filter(paid=True, status="paid").order_by("id")

    @classmethod
    def run(cls, limit=20, order_id=None, simulate_full_lifecycle=False):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limite invalide (1 a 100).")
        result = {"selected": 0, "prepared": 0, "submitted": 0, "blocked": 0, "failed": 0, "supplier_failed_existing": 0}
        if order_id is not None and (not isinstance(order_id, int) or order_id <= 0):
            raise ValueError("Identifiant de commande invalide.")
        orders = cls.get_orders()
        if order_id is not None:
            orders = orders.filter(id=order_id)
        for order in orders.iterator():
            if result["selected"] >= limit:
                break
            items = list(order.items.all())
            if not items or any(getattr(getattr(item.product, "source_opportunity", None), "supplier_offer", None) is None for item in items) or SupplierOrder.objects.filter(order=order, mode="sandbox", status="failed").exists():
                result["blocked"] += 1
                continue
            if result["selected"] >= limit:
                break
            result["selected"] += 1
            if not items:
                result["blocked"] += 1
                print("Commande", order.id, "- bloquee : aucun article")
                continue
            if any(getattr(getattr(item.product, "source_opportunity", None), "supplier_offer", None) is None for item in items):
                result["blocked"] += 1
                print("Commande", order.id, "- bloquee : offre fournisseur introuvable")
                continue
            try:
                if not all(SupplierPreparation.objects.filter(order_item=item).exists() for item in items):
                    SupplierPreparationRunner.run(order, source="automatic")
                    result["prepared"] += 1
                if not all(SupplierPreparation.objects.filter(order_item=item).exists() for item in items):
                    result["blocked"] += 1
                    print("Commande", order.id, "- bloquee : preparation fournisseur incomplete")
                    continue
                if SupplierOrder.objects.filter(order=order, mode="sandbox", status="failed").exists():
                    result["blocked"] += 1
                    print("Commande", order.id, "- bloquee : dossier fournisseur en echec")
                    continue
                existing_ids = set(SupplierOrder.objects.filter(order=order, mode="sandbox", status="submitted").values_list("id", flat=True))
                report = SupplierOrderSubmissionRunner.run_with_report(order, sandbox=True, retry_failed=False, source="automatic")
                result["submitted"] += sum(1 for dossier in report["supplier_orders"] if dossier.status == "submitted" and dossier.id not in existing_ids)
                result["failed"] += report["failed"]
            except (ValueError, OSError) as error:
                if isinstance(error, ValueError) and str(error) == "L\u0027offre fournisseur est introuvable.":
                    OrderProcessingEvent.objects.get_or_create(order=order, event_type="supplier_preparation_failed", defaults={"source": "automatic"})
                result["failed"] += 1
                print("Commande", order.id, "- erreur:", error)
        failed_existing = SupplierOrder.objects.filter(mode="sandbox", status="failed")
        if order_id is not None:
            failed_existing = failed_existing.filter(order_id=order_id)
        result["supplier_failed_existing"] = failed_existing.count()
        for dossier in failed_existing:
            print("Commande", dossier.order_id, "- dossier fournisseur", dossier.id, "- echec existant:", dossier.error_message)
        lifecycle = SupplierOrderLifecycleRunner.run(limit=limit, order_id=order_id, simulate_full_lifecycle=simulate_full_lifecycle)
        result["lifecycle_selected"] = lifecycle["selected"]
        result["lifecycle_processed"] = lifecycle["processed"]
        result["lifecycle_failed"] = lifecycle["failed"]
        result["lifecycle_skipped"] = lifecycle["skipped"]
        monitoring = SupplierOrderMonitoringRunner.run(limit=limit, order_id=order_id)
        result["monitor_selected"] = monitoring["selected"]
        result["monitor_synced"] = monitoring["synced"]
        result["monitor_failed"] = monitoring["failed"]
        return result
