from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from product_intelligence.models import (
    ProductIdea,
)
from product_intelligence.services.comparable_price_runner_factory import (
    ComparablePriceRunnerFactory,
)


class Command(BaseCommand):

    help = (
        "Recherche et enregistre des prix "
        "comparables pour les offres fournisseur "
        "d’une idée produit."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "idea_id",
            type=int,
            help=(
                "Identifiant de l’idée produit."
            ),
        )

        parser.add_argument(
            "--model",
            default=None,
            help=(
                "Modèle OpenAI à utiliser."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        idea_id = options[
            "idea_id"
        ]

        model = options[
            "model"
        ]

        try:
            product_idea = (
                ProductIdea.objects.get(
                    pk=idea_id,
                )
            )
        except ProductIdea.DoesNotExist as error:
            raise CommandError(
                "Idée produit introuvable."
            ) from error

        runner = (
            ComparablePriceRunnerFactory.build(
                model=model,
            )
        )

        summary = runner.run(
            product_idea=product_idea,
        )

        self.stdout.write(
            (
                f"{summary['offers_processed']} "
                "offre(s) fournisseur traitée(s)"
            )
        )

        self.stdout.write(
            (
                f"{summary['comparable_prices_saved']} "
                "prix comparable(s) enregistré(s)"
            )
        )