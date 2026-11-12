from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from product_intelligence.models import (
    ComparablePrice,
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
                f"{summary['offers_researched']} "
                "offre(s) admise(s) à la recherche "
                "de prix"
            )
        )

        self.stdout.write(
            (
                f"{summary['offers_incomplete']} "
                "offre(s) incomplète(s)"
            )
        )

        self.stdout.write(
            (
                f"{summary['offers_rejected']} "
                "offre(s) rejetée(s) pour la livraison"
            )
        )

        self.stdout.write(
            (
                f"{summary['offers_slow']} "
                "offre(s) avec livraison lente tolérée"
            )
        )

        self.stdout.write(
            (
                f"{summary['offers_fallback']} "
                "offre(s) de repli entre 21 et 50 jours"
            )
        )

        current_prices_count = (
            ComparablePrice.objects.filter(
                supplier_offer__product_idea=product_idea,
                is_current=True,
            ).count()
        )

        historical_prices_count = (
            ComparablePrice.objects.filter(
                supplier_offer__product_idea=product_idea,
                is_current=False,
            ).count()
        )

        self.stdout.write(
            (
                f"{summary['comparable_prices_saved']} "
                "prix comparable(s) créé(s) pendant "
                "cette collecte"
            )
        )

        self.stdout.write(
            (
                f"{current_prices_count} "
                "prix comparable(s) dans le(s) lot(s) "
                "actif(s)"
            )
        )

        self.stdout.write(
            (
                f"{historical_prices_count} "
                "prix comparable(s) historique(s) "
                "conservé(s)"
            )
        )

        self.stdout.write(
            (
                f"{summary['comparable_prices_retained']} "
                "prix comparable(s) retenu(s)"
            )
        )

        self.stdout.write(
            (
                f"{summary['comparable_prices_rejected']} "
                "prix comparable(s) rejeté(s)"
            )
        )
