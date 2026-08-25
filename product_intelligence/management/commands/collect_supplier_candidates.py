from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from product_intelligence.models import (
    ProductIdea,
)
from product_intelligence.services.supplier_candidate_collection_runner import (
    SupplierCandidateCollectionRunner,
)


class Command(BaseCommand):

    help = (
        "Collecte jusqu’à cinq offres par "
        "fournisseur pour une catégorie "
        "de produit sélectionnée."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "product_idea_id",
            type=int,
            help=(
                "Identifiant de la catégorie "
                "de produit sélectionnée."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        product_idea_id = options[
            "product_idea_id"
        ]

        try:
            product_idea = (
                ProductIdea.objects.get(
                    pk=product_idea_id,
                )
            )
        except ProductIdea.DoesNotExist as error:
            raise CommandError(
                (
                    "La catégorie de produit "
                    "est introuvable."
                )
            ) from error

        if product_idea.status != "selected":
            raise CommandError(
                (
                    "La catégorie doit être "
                    "sélectionnée."
                )
            )

        try:
            summary = (
                SupplierCandidateCollectionRunner
                .collect(
                    product_idea=product_idea,
                )
            )
        except ValueError as error:
            raise CommandError(
                str(error)
            ) from error

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{summary['suppliers_searched']} "
                    "fournisseur(s) interrogé(s)"
                )
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{summary['offers_found']} "
                    "offre(s) candidate(s)"
                )
            )
        )

        for supplier_name, offer_count in (
            summary[
                "offers_by_supplier"
            ].items()
        ):
            self.stdout.write(
                (
                    f"{supplier_name} : "
                    f"{offer_count}"
                )
            )