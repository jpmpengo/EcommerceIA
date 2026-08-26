import ssl

import httpx
import truststore
from django.db import transaction
from openai import OpenAI

from product_intelligence.models import (
    ProductIdea,
)
from product_intelligence.services.openai_client import (
    OpenAIClient,
)
from product_intelligence.services.product_idea_discovery import (
    ProductIdeaDiscoveryService,
)


class ProductIdeaGenerationService:

    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def generate(
        cls,
        model=None,
    ):
        if ProductIdea.objects.filter(
            status="proposed",
        ).exists():
            raise ValueError(
                (
                    "Des idées sont déjà "
                    "en attente d’examen."
                )
            )

        selected_model = (
            model
            or cls.DEFAULT_MODEL
        )

        discovery_service = (
            cls._build_discovery_service(
                model=selected_model,
            )
        )

        result = discovery_service.discover()
        ideas = result["ideas"]

        if len(ideas) != 5:
            raise ValueError(
                (
                    "OpenAI doit proposer "
                    "exactement cinq idées."
                )
            )

        cls._save_ideas(
            ideas=ideas,
            model=selected_model,
        )

        return len(ideas)

    @staticmethod
    def _build_discovery_service(
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
                        idea["customer_problem"]
                    ),
                    target_customer=(
                        idea["target_customer"]
                    ),
                    reason_to_study=(
                        idea["reason_to_study"]
                    ),
                    countries=idea["countries"],
                    search_keywords=(
                        idea["search_keywords"]
                    ),
                    supplier_search_keywords=(
                        idea[
                            "supplier_search_keywords"
                        ]
                    ),
                    demand_signals=(
                        idea["demand_signals"]
                    ),
                    evidence_sources=(
                        idea["evidence_sources"]
                    ),
                    source="openai",
                    model_name=model,
                    status="proposed",
                )
                for idea in ideas
            ]
        )