from openai import OpenAI

from django.core.management.base import (
    BaseCommand,
)

from product_intelligence.services.openai_client import (
    OpenAIClient,
)
from product_intelligence.services.product_idea_discovery import (
    ProductIdeaDiscoveryService,
)

import ssl

import httpx
import truststore
from openai import OpenAI

from django.db import transaction

from product_intelligence.models import (
    ProductIdea,
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
            default="gpt-5.6-luna",
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
        model = options["model"]

        service = self._build_service(
            model
        )

        result = service.discover()

        ideas = result["ideas"]

        self._save_ideas(
            ideas=ideas,
            model=model,
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"{len(ideas)} "
                    "idée(s) proposée(s)"
                )
            )
        )

        for index, idea in enumerate(
            ideas,
            start=1,
        ):
            countries = ", ".join(
                idea["countries"]
            )

            keywords = ", ".join(
                idea["search_keywords"]
            )

            self.stdout.write("")

            self.stdout.write(
                (
                    f"{index}. "
                    f"{idea['name']}"
                )
            )

            self.stdout.write(
                (
                    "   Problème client : "
                    f"{idea['customer_problem']}"
                )
            )

            self.stdout.write(
                (
                    "   Client cible : "
                    f"{idea['target_customer']}"
                )
            )

            self.stdout.write(
                (
                    "   Pourquoi l'étudier : "
                    f"{idea['reason_to_study']}"
                )
            )

            self.stdout.write(
                (
                    "   Pays : "
                    f"{countries}"
                )
            )

            self.stdout.write(
                (
                    "   Mots-clés : "
                    f"{keywords}"
                )
            )

    @staticmethod
    @transaction.atomic
    def _save_ideas(
        ideas,
        model,
    ):
        ProductIdea.objects.bulk_create(
            [
                ProductIdea(
                    name=idea["name"],
                    customer_problem=(
                        idea[
                            "customer_problem"
                        ]
                    ),
                    target_customer=(
                        idea[
                            "target_customer"
                        ]
                    ),
                    reason_to_study=(
                        idea[
                            "reason_to_study"
                        ]
                    ),
                    countries=(
                        idea["countries"]
                    ),
                    search_keywords=(
                        idea[
                            "search_keywords"
                        ]
                    ),
                    source="openai",
                    model_name=model,
                    status="proposed",
                )
                for idea in ideas
            ]
        )

    def _build_service(
        self,
        model,
    ):
        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        http_client = httpx.Client(
            verify=ssl_context,
            timeout=60.0,
        )

        sdk_client = OpenAI(
            http_client=http_client
        )

        client = OpenAIClient(
            client=sdk_client,
            model=model,
        )

        return ProductIdeaDiscoveryService(
            client=client
        )
