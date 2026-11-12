from orders.models import Order, SupplierPreparation
from orders.services.supplier_preparation_runner import SupplierPreparationRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelinePreparationStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        for order in Order.objects.filter(paid=True).order_by("id"):
            items = list(order.items.select_related("product").all())
            if not items:
                continue
            missing = [item for item in items if not SupplierPreparation.objects.filter(order_item=item).exists()]
            if not missing:
                continue
            if any(getattr(getattr(item.product, "source_opportunity", None), "supplier_offer", None) is None for item in missing):
                result.incidents.append("Commande {} : offre fournisseur introuvable".format(order.id))
                continue
            before = len(missing)
            try:
                SupplierPreparationRunner.run(order, source="automatic")
            except Exception as error:
                result.incidents.append("Commande {} : preparation impossible - {}".format(order.id, error))
                continue
            remaining = sum(not SupplierPreparation.objects.filter(order_item=item).exists() for item in items)
            result.operations_effectuees += before - remaining
            if remaining:
                result.incidents.append("Commande {} : {} preparation(s) manquante(s)".format(order.id, remaining))
        return result
