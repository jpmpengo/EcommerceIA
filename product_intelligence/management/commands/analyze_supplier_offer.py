from decimal import Decimal
from pprint import pformat

from django.core.management.base import BaseCommand, CommandError

from product_intelligence.models import SupplierOffer
from product_intelligence.services.supplier_offer_analysis_runner import (
    SupplierOfferAnalysisRunner,
)


class Command(BaseCommand):
    help = "Analyse une offre fournisseur et crée éventuellement l’opportunité."

    def add_arguments(self, parser):
        parser.add_argument("offer_id", type=int)
        parser.add_argument("--create", action="store_true")
        parser.add_argument("--currency", default="EUR")
        parser.add_argument("--vat-rate", default="0.20")
        parser.add_argument("--minimum-profit", default="0.01")
        parser.add_argument("--minimum-margin-rate", default="10.00")
        parser.add_argument("--payment-rate", default="0.015")
        parser.add_argument("--payment-fixed-fee", default="0.25")
        parser.add_argument("--return-reserve-rate", default="0.05")
        parser.add_argument("--safety-reserve-rate", default="0.05")

    def handle(self, *args, **options):
        try:
            offer = SupplierOffer.objects.select_related(
                "supplier"
            ).get(pk=options["offer_id"])
        except SupplierOffer.DoesNotExist as error:
            raise CommandError("Offre fournisseur introuvable.") from error

        runner = SupplierOfferAnalysisRunner(
            market_currency=options["currency"],
            minimum_profit=Decimal(
                options["minimum_profit"]
            ),
            minimum_margin_rate=Decimal(
                options["minimum_margin_rate"]
            ),
            vat_rate=Decimal(options["vat_rate"]),
            payment_rate=Decimal(
                options["payment_rate"]
            ),
            payment_fixed_fee=Decimal(
                options["payment_fixed_fee"]
            ),
            return_reserve_rate=Decimal(
                options["return_reserve_rate"]
            ),
            safety_reserve_rate=Decimal(
                options["safety_reserve_rate"]
            ),
        )

        result = runner.process(
            supplier_offer=offer,
            create=options["create"],
        )

        printable = dict(result)
        opportunity = printable.pop("opportunity")
        printable["opportunity_id"] = (
            opportunity.pk
            if opportunity is not None
            else None
        )
        self.stdout.write(pformat(printable))
