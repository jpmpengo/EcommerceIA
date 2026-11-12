from urllib.parse import urlparse
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from orders.services.nightly_order_pipeline_runner import NightlyOrderPipelineRunner


class Command(BaseCommand):
    help = "Lance le pipeline nocturne post-paiement EcommerceIA."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--order-id", type=int, default=None)
        parser.add_argument("--simulate-full-lifecycle", action="store_true")
        parser.add_argument("--send-notifications", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if options["dry_run"]:
            from orders.models import Order, SupplierOrder
            orders = Order.objects.filter(paid=True, status="paid").order_by("id")
            if options["order_id"] is not None:
                orders = orders.filter(id=options["order_id"])
            self.stdout.write("SIMULATION NOCTURNE - AUCUNE EXECUTION")
            for order in orders[:options["limit"]]:
                items = list(order.items.select_related("product"))
                missing = not items or any(getattr(getattr(item.product, "source_opportunity", None), "supplier_offer", None) is None for item in items)
                failed = SupplierOrder.objects.filter(order=order, mode="sandbox", status="failed").exists()
                status = "BLOQUEE : offre fournisseur absente" if missing else "BLOQUEE : dossier fournisseur en echec" if failed else "A EXAMINER : preparation ou soumission"
                self.stdout.write("Commande {} : {}".format(order.id, status))
            from orders.services.supplier_order_lifecycle_runner import SupplierOrderLifecycleRunner
            from orders.services.supplier_order_monitoring_runner import SupplierOrderMonitoringRunner
            lifecycle = SupplierOrderLifecycleRunner.get_orders()
            monitoring = SupplierOrderMonitoringRunner.get_due_orders()
            if options["order_id"] is not None:
                lifecycle = lifecycle.filter(order_id=options["order_id"])
                monitoring = monitoring.filter(order_id=options["order_id"])
            self.stdout.write("Cycle fournisseur - dossiers a examiner : {}".format(lifecycle.count()))
            self.stdout.write("Surveillance logistique - dossiers a verifier : {}".format(monitoring.count()))
            self.stdout.write("Cycle fournisseur - IDs : {}".format(list(lifecycle.values_list("id", flat=True)[:options["limit"]])))
            self.stdout.write("Surveillance logistique - IDs : {}".format(list(monitoring.values_list("id", flat=True)[:options["limit"]])))
            from orders.services.reception_monitoring_runner import ReceptionMonitoringRunner
            notifications = ReceptionMonitoringRunner.get_orders_to_notify()
            receptions = ReceptionMonitoringRunner.get_due_orders()
            if options["order_id"] is not None:
                notifications = notifications.filter(id=options["order_id"])
                receptions = receptions.filter(id=options["order_id"])
            self.stdout.write("Notifications de reception possibles : {}".format(notifications.count()))
            self.stdout.write("Receptions presumees a examiner : {}".format(receptions.count()))
            self.stdout.write("Notifications - commandes : {}".format(list(notifications.values_list("id", flat=True)[:options["limit"]])))
            self.stdout.write("Receptions presumees - commandes : {}".format(list(receptions.values_list("id", flat=True)[:options["limit"]])))
            return
        settings.ORDER_RECEPTION_AUTO_EMAIL_ENABLED = True
        settings.ORDER_RECEPTION_TEST_MODE = True
        send = True
        test_mode = True
        site_url = None
        if send:
            if not getattr(settings, "ORDER_RECEPTION_AUTO_EMAIL_ENABLED", False):
                raise CommandError("Notifications automatiques desactivees.")
            site_url = "http://127.0.0.1:8000" if test_mode else getattr(settings, "ORDER_RECEPTION_SITE_URL", "")
            parsed = urlparse(site_url)
            if test_mode and getattr(settings, "ORDER_RECEPTION_TEST_EMAIL", "") != "jpmpengo@yahoo.fr":
                raise CommandError("Adresse de test non autorisee.")
            if not test_mode and (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
                raise CommandError("URL publique HTTPS requise.")
        try:
            result = NightlyOrderPipelineRunner.run(limit=options["limit"], order_id=options["order_id"], simulate_full_lifecycle=options["simulate_full_lifecycle"], send_notifications=send, site_url=site_url)
        except ValueError as error:
            raise CommandError(str(error)) from error
        for section, report in result.items():
            self.stdout.write("{} : {}".format(section, report))
