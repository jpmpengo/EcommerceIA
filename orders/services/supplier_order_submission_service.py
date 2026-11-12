from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from orders.models import OrderProcessingEvent, SupplierOrder, SupplierOrderItem, SupplierPreparation


class SupplierOrderSubmissionService:
    def __init__(self, adapter_factory):
        self.adapter_factory = adapter_factory

    def submit(self, order, sandbox=True, retry_failed=False, source="automatic"):
        if not sandbox:
            raise ValueError("La transmission fournisseur réelle est désactivée.")
        if not order.paid:
            raise ValueError("La commande client doit être payée.")

        groups = defaultdict(list)
        incomplete_supplier_ids = set()
        for item in order.items.select_related("product").all():
            try:
                preparation = item.supplier_preparation
            except SupplierPreparation.DoesNotExist:
                opportunity = getattr(item.product, "source_opportunity", None)
                offer = getattr(opportunity, "supplier_offer", None)
                if offer is None:
                    raise ValueError("Soumission suspendue : fournisseur indetermine pour un article sans preparation.")
                incomplete_supplier_ids.add(offer.supplier_id)
                print("Commande", order.id, "- article", item.id, "- preparation fournisseur manquante")
                continue
            groups[preparation.supplier_offer.supplier].append(preparation)

        results = []
        self.last_submission_failed_count = 0
        for supplier, preparations in groups.items():
            if supplier.id in incomplete_supplier_ids:
                self.last_submission_failed_count += 1
                print("Commande", order.id, "- fournisseur", supplier.id, "- soumission bloquee : preparation incomplete")
                continue
            if SupplierPreparation.objects.filter(order_item__order=order, supplier_offer__supplier=supplier).count() != len(preparations):
                self.last_submission_failed_count += 1
                print("Commande", order.id, "- fournisseur", supplier.id, "- preparations incoherentes")
                continue
            try:
                results.append(
                    self._submit_group(
                        order,
                        supplier,
                        preparations,
                        sandbox,
                        retry_failed,
                        source,
                    )
                )
            except Exception as error:
                self.last_submission_failed_count += 1
                print("Commande", order.id, "- fournisseur", supplier.id, "- erreur:", error)
        return results

    def _submit_group(
        self,
        order,
        supplier,
        preparations,
        sandbox,
        retry_failed,
        source,
    ):
        mode = "sandbox" if sandbox else "production"
        key = f"ECOMMERCEIA-{order.id}-{supplier.id}-{mode.upper()}"
        supplier_order, _ = SupplierOrder.objects.get_or_create(
            order=order,
            supplier=supplier,
            mode=mode,
            defaults={"idempotency_key": key},
        )
        if supplier_order.status == "submitted":
            return supplier_order
        if order.status != "paid":
            raise ValueError("Nouvelle soumission interdite : commande client deja avancee.")
        if supplier_order.status == "failed" and not retry_failed:
            raise ValueError(
                "Une tentative fournisseur a échoué et doit être vérifiée avant toute relance."
            )
        if supplier_order.status == "failed":
            supplier_order.status = "pending"
            supplier_order.error_message = ""
            supplier_order.save(update_fields=["status", "error_message"])

        for preparation in preparations:
            SupplierOrderItem.objects.get_or_create(
                supplier_order=supplier_order,
                order_item=preparation.order_item,
                defaults={"supplier_preparation": preparation},
            )

        adapter = self.adapter_factory.create(supplier, sandbox=sandbox)
        payload = adapter.build_payload(supplier_order, preparations)
        supplier_order.request_payload = payload
        supplier_order.tracking_provider = payload.get("logisticName", "")
        supplier_order.save(update_fields=["request_payload", "tracking_provider"])

        try:
            response = adapter.submit(payload)
        except Exception as error:
            supplier_order.status = "failed"
            supplier_order.error_message = str(error)
            supplier_order.save(update_fields=["status", "error_message"])
            raise

        supplier_order_id = str(response.get("orderId") or "")
        if not supplier_order_id:
            supplier_order.status = "failed"
            supplier_order.response_payload = response
            supplier_order.error_message = "CJ n'a retourné aucun identifiant de commande."
            supplier_order.save(
                update_fields=["status", "response_payload", "error_message"]
            )
            raise ValueError(supplier_order.error_message)

        with transaction.atomic():
            supplier_order.status = "submitted"
            supplier_order.supplier_order_id = supplier_order_id
            supplier_order.response_payload = response
            supplier_order.error_message = ""
            supplier_order.submitted_at = timezone.now()
            supplier_order.save(
                update_fields=[
                    "status",
                    "supplier_order_id",
                    "response_payload",
                    "error_message",
                    "submitted_at",
                ]
            )
            OrderProcessingEvent.objects.create(
                order=order,
                supplier_order=supplier_order,
                event_type="supplier_order_submitted",
                source=source,
            )
        return supplier_order
