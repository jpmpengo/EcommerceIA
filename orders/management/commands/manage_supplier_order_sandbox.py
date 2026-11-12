import os
import ssl

import httpx
import truststore
from django.core.management.base import BaseCommand, CommandError

from orders.models import SupplierOrder
from orders.services.supplier_order_adapter_factory import SupplierOrderAdapterFactory
from orders.services.supplier_order_lifecycle_service import SupplierOrderLifecycleService
from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient


class Command(BaseCommand):
    help = "Consulte ou fait progresser un dossier fournisseur sandbox."

    def add_arguments(self, parser):
        parser.add_argument("supplier_order_id", type=int)
        actions = parser.add_mutually_exclusive_group(required=True)
        actions.add_argument("--sync", action="store_true")
        actions.add_argument(
            "--confirm",
            action="store_true",
            help="Confirme une commande CREATED (100) pour la passer à UNPAID (200).",
        )
        actions.add_argument("--pay", action="store_true")
        actions.add_argument("--status", type=int, choices=[400, 500, 600, 700])
        actions.add_argument("--tracking")

    def handle(self, *args, **options):
        try:
            supplier_order = SupplierOrder.objects.select_related("supplier").get(
                id=options["supplier_order_id"]
            )
        except SupplierOrder.DoesNotExist as error:
            raise CommandError("Dossier fournisseur introuvable.") from error

        api_key = os.getenv("CJ_API_KEY", "")
        if not api_key:
            raise CommandError("CJ_API_KEY est manquante.")

        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=context, timeout=30.0) as http_client:
            try:
                token = CJAuthClient(api_key, http_client).get_access_token()
                service = SupplierOrderLifecycleService(
                    SupplierOrderAdapterFactory(
                        cj_client=CJClient(token, http_client),
                    )
                )
                if options["sync"]:
                    detail = service.sync(supplier_order)
                    action = "SYNCHRONISATION"
                elif options["confirm"]:
                    detail = service.confirm(supplier_order, source="manual")
                    action = "CONFIRMATION"
                elif options["pay"]:
                    detail = service.simulate_pay(supplier_order, source="manual")
                    action = "PAIEMENT SIMULE"
                elif options["status"] is not None:
                    detail = service.update_status(
                        supplier_order,
                        options["status"],
                        source="manual",
                    )
                    action = f"STATUT {options['status']}"
                else:
                    detail = service.update_tracking(
                        supplier_order,
                        options["tracking"],
                        source="manual",
                    )
                    action = "SUIVI FICTIF"
            except ValueError as error:
                raise CommandError(str(error)) from error

        supplier_order.refresh_from_db()
        self.stdout.write(f"ACTION: {action}")
        self.stdout.write(f"DOSSIER: {supplier_order.id}")
        self.stdout.write(f"COMMANDE CJ: {supplier_order.supplier_order_id}")
        self.stdout.write(f"STATUT CJ: {supplier_order.supplier_status or 'NON RENSEIGNE'}")
        self.stdout.write(
            f"SOUS-STATUT CJ: {supplier_order.supplier_sub_status or 'NON RENSEIGNE'}"
        )
        self.stdout.write(
            f"SUIVI: {supplier_order.tracking_number or 'NON RENSEIGNE'}"
        )
        self.stdout.write(f"SANDBOX CJ: {detail.get('isSandbox')}")
        self.stdout.write(
            self.style.SUCCESS("AUCUN DEBIT, AUCUNE EXPEDITION REELLE")
        )
