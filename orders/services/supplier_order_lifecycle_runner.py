from orders.models import SupplierOrder


class SupplierOrderLifecycleRunner:
    @classmethod
    def run(cls, limit=20, order_id=None, simulate_full_lifecycle=False):
        from orders.services.supplier_order_sandbox_runner import SupplierOrderSandboxRunner

        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limite invalide (1 a 100).")

        result = {"selected": 0, "processed": 0, "failed": 0, "skipped": 0}

        dossiers = cls.get_orders()
        if order_id is not None:
            dossiers = dossiers.filter(order_id=order_id)
        for dossier in dossiers[:limit]:
            result["selected"] += 1
            if dossier.error_message:
                result["skipped"] += 1
                continue
            try:
                completed = 0
                for step in range(8 if simulate_full_lifecycle else 5):
                    dossier.refresh_from_db()
                    if dossier.supplier_status == "DELIVERED":
                        break
                    action = cls.next_action(dossier, simulate_full_lifecycle=simulate_full_lifecycle)
                    if action is None:
                        break
                    if action == "pay":
                        SupplierOrderSandboxRunner.run(dossier, "sync")
                        dossier.refresh_from_db()
                        if dossier.supplier_status != "UNPAID":
                            continue
                    before = (dossier.supplier_status, dossier.supplier_sub_status)
                    if action == "tracking":
                        if dossier.mode != "sandbox":
                            raise ValueError("Suivi fictif interdit hors simulation sandbox.")
                        tracking_number = "SANDBOX-ECOMMERCEIA-{}-{}".format(dossier.order_id, dossier.id)
                        SupplierOrderSandboxRunner.run(dossier, action, tracking_number=tracking_number)
                    elif action == "deliver":
                        if dossier.mode != "sandbox" or dossier.supplier_status != "SHIPPED" or not dossier.tracking_number:
                            raise ValueError("Livraison simulee interdite : conditions sandbox non remplies.")
                        SupplierOrderSandboxRunner.run(dossier, action)
                    else:
                        SupplierOrderSandboxRunner.run(dossier, action)
                    completed += 1
                    result["processed"] += 1
                    dossier.refresh_from_db()
                    after = (dossier.supplier_status, dossier.supplier_sub_status)
                    if action == "sync" and after == before:
                        break
                if completed == 0:
                    result["skipped"] += 1
            except Exception as error:
                dossier.error_message = str(error)[:2000]
                dossier.save(update_fields=["error_message"])
                result["failed"] += 1
                print("Dossier fournisseur", dossier.id, "- erreur:", error)

        return result

    @staticmethod
    def next_action(supplier_order, simulate_full_lifecycle=False):
        from orders.models import OrderProcessingEvent

        if not supplier_order.supplier_status:
            return "sync"

        if supplier_order.supplier_status == "IN_CART":
            return "sync"

        if supplier_order.supplier_status == "DELIVERED":
            return None
        if supplier_order.supplier_status == "SHIPPED":
            if supplier_order.mode == "sandbox":
                return "deliver" if supplier_order.tracking_number else "tracking"
            return "sync"

        if supplier_order.supplier_status not in {"CREATED", "UNPAID", "UNSHIPPED"}:
            return None

        events = set(OrderProcessingEvent.objects.filter(
            supplier_order=supplier_order,
        ).values_list("event_type", flat=True))

        if "supplier_order_submitted" not in events:
            return None

        if events.intersection({"supplier_shipped", "supplier_delivered"}):
            return "sync"
        if supplier_order.supplier_sub_status == "PROCESSING":
            return "ship" if "supplier_processing_started" in events else "sync"

        if "supplier_processing_started" in events:
            return "ship" if supplier_order.supplier_sub_status == "PROCESSING" else "sync"

        if "supplier_payment_completed" in events and "supplier_order_confirmed" not in events:
            return "sync"

        if "supplier_order_confirmed" not in events and supplier_order.supplier_status == "CREATED":
            return "confirm"
        if "supplier_payment_completed" not in events and supplier_order.supplier_status == "UNPAID":
            return "sync" if supplier_order.supplier_sub_status == "PROCESSING" else "pay"
        if "supplier_processing_started" not in events:
            return "sync" if supplier_order.supplier_sub_status == "PROCESSING" else "processing"
        return "sync"

    @staticmethod
    def get_orders():
        return (
            SupplierOrder.objects.filter(
                mode="sandbox",
                status="submitted",
                supplier__name__iexact="cjdropshipping",
            )
            .exclude(supplier_status="DELIVERED")
            .select_related("order", "supplier")
            .order_by("id")
        )
