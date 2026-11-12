from time import perf_counter

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
        started_at = perf_counter()

        generated_count = (
            ProductIdeaGenerationService
            .generate(
                model=options["model"],
            )
        )

        elapsed_seconds = perf_counter() - started_at

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{generated_count} "
                    "idée(s) proposée(s) - "
                    f"{elapsed_seconds:.1f} seconde(s)"
                )
            )
        )
