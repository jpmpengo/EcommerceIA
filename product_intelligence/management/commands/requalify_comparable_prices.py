from django.core.management.base import BaseCommand

from product_intelligence.models import SupplierOffer
from product_intelligence.services.comparable_price_qualification import (
    ComparablePriceQualificationService,
)


class Command(BaseCommand):
    help = "Requalifie les prix comparables avec les règles de variante."

    def add_arguments(self, parser):
        parser.add_argument("offer_ids", nargs="*", type=int)

    def handle(self, *args, **options):
        offers = SupplierOffer.objects.filter(
            comparable_prices__isnull=False
        ).distinct().order_by("id")
        if options["offer_ids"]:
            offers = offers.filter(id__in=options["offer_ids"])

        totals = {"examined": 0, "retained": 0, "rejected": 0}
        for offer in offers:
            result = ComparablePriceQualificationService.qualify(offer)
            for key in totals:
                totals[key] += result[key]
            self.stdout.write(
                f"OFFRE {offer.id}: {result['retained']} retenu(s), "
                f"{result['rejected']} rejeté(s)"
            )

        self.stdout.write(
            "TOTAL: "
            f"{totals['examined']} examiné(s), "
            f"{totals['retained']} retenu(s), "
            f"{totals['rejected']} rejeté(s)"
        )
