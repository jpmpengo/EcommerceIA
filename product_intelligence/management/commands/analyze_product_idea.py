from pprint import pformat

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from product_intelligence.models import ProductIdea
from product_intelligence.services.product_idea_manual_analysis import (
    ProductIdeaManualAnalysisService,
)


class Command(BaseCommand):
    help = (
        "Étudie manuellement une idée sélectionnée "
        "et crée au plus une opportunité par fournisseur."
    )

    def add_arguments(self, parser):
        parser.add_argument("idea_id", type=int)

    def handle(self, *args, **options):
        try:
            idea = ProductIdea.objects.get(
                pk=options["idea_id"]
            )
        except ProductIdea.DoesNotExist as error:
            raise CommandError(
                "Idée produit introuvable."
            ) from error

        try:
            result = (
                ProductIdeaManualAnalysisService.run(
                    product_idea=idea
                )
            )
        except ValueError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(pformat(result))
