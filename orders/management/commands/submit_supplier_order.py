from django.core.management.base import BaseCommand, CommandError

from orders.models import Order
from orders.services.supplier_order_submission_runner import SupplierOrderSubmissionRunner


class Command(BaseCommand):
    help = "Transmet les dossiers fournisseurs d'une commande (sandbox uniquement)."

    def add_arguments(self, parser):
        parser.add_argument("order_id", type=int)
        parser.add_argument("--sandbox", action="store_true")
        parser.add_argument("--retry-failed", action="store_true")

    def handle(self, *args, **options):
        if not options["sandbox"]:
            raise CommandError(
                "Mode réel désactivé. Relancez explicitement avec --sandbox."
            )
        try:
            order = Order.objects.prefetch_related(
                "items__product",
                "items__supplier_preparation__supplier_offer__supplier",
            ).get(id=options["order_id"])
        except Order.DoesNotExist as error:
            raise CommandError("Commande introuvable.") from error

        try:
            supplier_orders = SupplierOrderSubmissionRunner.run(
                order,
                sandbox=True,
                retry_failed=options["retry_failed"],
                source="manual",
            )
        except ValueError as error:
            raise CommandError(str(error)) from error

        for supplier_order in supplier_orders:
            self.stdout.write(f"DOSSIER FOURNISSEUR: {supplier_order.id}")
            self.stdout.write(f"FOURNISSEUR: {supplier_order.supplier.name}")
            self.stdout.write(f"MODE: {supplier_order.mode.upper()}")
            self.stdout.write(f"STATUT: {supplier_order.status.upper()}")
            self.stdout.write(f"COMMANDE FOURNISSEUR: {supplier_order.supplier_order_id}")
        self.stdout.write(
            self.style.SUCCESS(
                "TEST SANDBOX TERMINE — AUCUN DEBIT, AUCUNE EXPEDITION REELLE"
            )
        )
