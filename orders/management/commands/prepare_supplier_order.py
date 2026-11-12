from django.core.management.base import BaseCommand, CommandError

from orders.models import Order
from orders.services.supplier_preparation_runner import SupplierPreparationRunner


class Command(BaseCommand):
    help = "Prépare une commande fournisseur en simulation, sans transmission."

    def add_arguments(self, parser):
        parser.add_argument("order_id", type=int)
        parser.add_argument("--vat-rate", default="0.20")

    def handle(self, *args, **options):
        try:
            order = Order.objects.prefetch_related("items__product").get(
                id=options["order_id"]
            )
        except Order.DoesNotExist as error:
            raise CommandError("Commande introuvable.") from error

        try:
            preparations = SupplierPreparationRunner.run(
                order,
                source="manual",
                vat_rate=options["vat_rate"],
            )
        except ValueError as error:
            raise CommandError(str(error)) from error

        for preparation in preparations:
            self.stdout.write(f"DOSSIER: {preparation.id}")
            self.stdout.write(f"ARTICLE: {preparation.order_item.product.name}")
            self.stdout.write(f"MODE: {preparation.mode.upper()}")
            self.stdout.write(f"PAYS: {preparation.destination_country}")
            self.stdout.write(f"COUT DE BASE: {preparation.base_cost} {preparation.target_currency}")
            self.stdout.write(f"DOUANE ESTIMEE: {preparation.import_duty} {preparation.target_currency}")
            self.stdout.write(f"REGLE DOUANIERE: {preparation.import_duty_method}")
            self.stdout.write(f"DATE DE REGLE: {preparation.import_duty_rule_date}")
            self.stdout.write("IOSS: NON VERIFIE")
            self.stdout.write("FRAIS DE DOSSIER TRANSPORTEUR: INCONNUS ET NON INCLUS")
            self.stdout.write(f"COUT RENDU: {preparation.landed_cost} {preparation.target_currency}")
            self.stdout.write(f"VENTE TTC: {preparation.sale_ttc} {preparation.target_currency}")
            self.stdout.write(f"VENTE NETTE HT: {preparation.net_revenue} {preparation.target_currency}")
            self.stdout.write(f"ACHATS ET CHARGES: {preparation.total_costs} {preparation.target_currency}")
            self.stdout.write(f"MARGE PREVISIONNELLE: {preparation.projected_profit} {preparation.target_currency}")
        self.stdout.write(self.style.SUCCESS("AUCUNE COMMANDE FOURNISSEUR TRANSMISE"))
