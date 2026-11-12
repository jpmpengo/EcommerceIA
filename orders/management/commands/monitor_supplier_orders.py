from django.core.management.base import BaseCommand, CommandError

from orders.services.supplier_order_monitoring_runner import SupplierOrderMonitoringRunner
from orders.services.supplier_monitor_lock import supplier_monitor_lock


class Command(BaseCommand):
    help = "Surveille les commandes fournisseur arrivees a echeance (sandbox)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            with supplier_monitor_lock() as acquired:
                if not acquired:
                    self.stdout.write("Surveillance deja en cours : execution ignoree.")
                    return
                if options["dry_run"]:
                    limit = options["limit"]
                    if not 1 <= limit <= 100:
                        raise ValueError("Limite invalide (1 a 100).")
                    dossiers = list(SupplierOrderMonitoringRunner.get_due_orders()[:limit])
                    self.stdout.write("SIMULATION - aucun appel fournisseur")
                    self.stdout.write("Dossiers selectionnes : {}".format(len(dossiers)))
                    self.stdout.write("IDs : {}".format([d.id for d in dossiers]))
                    return
                result = SupplierOrderMonitoringRunner.run(limit=options["limit"])
        except ValueError as error:
            raise CommandError(str(error)) from error
        self.stdout.write("Dossiers selectionnes : {}".format(result["selected"]))
        self.stdout.write("Synchronisations reussies : {}".format(result["synced"]))
        self.stdout.write("Erreurs : {}".format(result["failed"]))
