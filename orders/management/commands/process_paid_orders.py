from django.core.management.base import BaseCommand, CommandError
from orders.services.paid_order_pipeline_runner import PaidOrderPipelineRunner


class Command(BaseCommand):
    help = "Lance le pipeline post-paiement EcommerceIA (preparation uniquement pour le moment)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--order-id", type=int, default=None)
        parser.add_argument("--simulate-full-lifecycle", action="store_true", default=False)

    def handle(self, *args, **options):
        try:
            result = PaidOrderPipelineRunner.run(limit=options["limit"], order_id=options["order_id"], simulate_full_lifecycle=options["simulate_full_lifecycle"])
        except ValueError as error:
            raise CommandError(str(error)) from error
        self.stdout.write("Commandes selectionnees : {}".format(result["selected"]))
        self.stdout.write("Commandes preparees : {}".format(result["prepared"]))
        self.stdout.write("Commandes soumises : {}".format(result["submitted"]))
        self.stdout.write("Cycle fournisseur - dossiers selectionnes : {}".format(result["lifecycle_selected"]))
        self.stdout.write("Cycle fournisseur - etapes traitees : {}".format(result["lifecycle_processed"]))
        self.stdout.write("Cycle fournisseur - echecs : {}".format(result["lifecycle_failed"]))
        self.stdout.write("Cycle fournisseur - ignores : {}".format(result["lifecycle_skipped"]))
        self.stdout.write("Surveillance - dossiers : {}".format(result["monitor_selected"]))
        self.stdout.write("Surveillance - synchronises : {}".format(result["monitor_synced"]))
        self.stdout.write("Surveillance - erreurs : {}".format(result["monitor_failed"]))
        self.stdout.write("Commandes bloquees : {}".format(result["blocked"]))
        self.stdout.write("Erreurs : {}".format(result["failed"]))
