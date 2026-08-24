from django.core.management.base import (
    BaseCommand,
)

from product_intelligence.services.product_idea_generation import (
    ProductIdeaGenerationService,
)


class Command(BaseCommand):

    help = (
        "Propose cinq idées de produits "
        "à étudier avec OpenAI."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--model",
            default=(
                ProductIdeaGenerationService
                .DEFAULT_MODEL
            ),
            help=(
                "Modèle OpenAI utilisé pour "
                "la découverte."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        generated_count = (
            ProductIdeaGenerationService
            .generate(
                model=options["model"],
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{generated_count} "
                    "idée(s) proposée(s)"
                )
            )
        )