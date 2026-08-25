from unittest.mock import patch

from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)
from product_intelligence.services.product_idea_generation import (
    ProductIdeaGenerationService,
)


class ProductIdeaGenerationServiceTests(TestCase):

    @patch.object(
        ProductIdeaGenerationService,
        "_build_discovery_service",
    )
    def test_generate_rejects_when_proposed_ideas_exist(
        self,
        mock_build,
    ):
        ProductIdea.objects.create(
            name="Idée existante",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=[
                "FR",
            ],
            search_keywords=[
                "requête ciblée",
            ],
            source="openai",
            model_name="test-model",
            status="proposed",
        )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Des idées sont déjà "
                "en attente d’examen."
            ),
        ):
            ProductIdeaGenerationService.generate()

        mock_build.assert_not_called()

    @patch.object(
        ProductIdeaGenerationService,
        "_build_discovery_service",
    )
    def test_generate_saves_five_proposed_ideas(
        self,
        mock_build,
    ):
        discovery_service = (
            mock_build.return_value
        )

        discovery_service.discover.return_value = {
            "ideas": [
                {
                    "name": f"Idée {number}",
                    "customer_problem": (
                        f"Problème {number}."
                    ),
                    "target_customer": (
                        f"Client {number}."
                    ),
                    "reason_to_study": (
                        f"Raison {number}."
                    ),
                    "countries": [
                        "FR",
                        "BE",
                        "ES",
                    ],
                    "search_keywords": [
                        f"requête {number}",
                    ],
                    "demand_signals": [
                        (
                            "Signal de demande "
                            f"{number}."
                        ),
                    ],
                    "evidence_sources": [
                        {
                            "title": (
                                f"Source {number}"
                            ),
                            "url": (
                                "https://example.com/"
                                f"source-{number}"
                            ),
                            "evidence": (
                                "Cette source confirme "
                                "un intérêt public."
                            ),
                        },
                    ],
                }
                for number in range(
                    1,
                    6,
                )
            ],
        }

        generated_count = (
            ProductIdeaGenerationService
            .generate(
                model="test-model",
            )
        )

        self.assertEqual(
            generated_count,
            5,
        )

        self.assertEqual(
            ProductIdea.objects.count(),
            5,
        )

        self.assertEqual(
            ProductIdea.objects.filter(
                status="proposed",
                source="openai",
                model_name="test-model",
            ).count(),
            5,
        )

        first_idea = (
            ProductIdea.objects
            .order_by("id")
            .first()
        )

        self.assertEqual(
            first_idea.demand_signals,
            [
                "Signal de demande 1.",
            ],
        )

        self.assertEqual(
            first_idea.evidence_sources,
            [
                {
                    "title": "Source 1",
                    "url": (
                        "https://example.com/"
                        "source-1"
                    ),
                    "evidence": (
                        "Cette source confirme "
                        "un intérêt public."
                    ),
                },
            ],
        )

    @patch.object(
        ProductIdeaGenerationService,
        "_build_discovery_service",
    )
    def test_generate_rejects_incomplete_result(
        self,
        mock_build,
    ):
        discovery_service = (
            mock_build.return_value
        )

        discovery_service.discover.return_value = {
            "ideas": [
                {
                    "name": f"Idée {number}",
                    "customer_problem": (
                        f"Problème {number}."
                    ),
                    "target_customer": (
                        f"Client {number}."
                    ),
                    "reason_to_study": (
                        f"Raison {number}."
                    ),
                    "countries": [
                        "FR",
                    ],
                    "search_keywords": [
                        f"requête {number}",
                    ],
                }
                for number in range(
                    1,
                    5,
                )
            ],
        }

        with self.assertRaisesMessage(
            ValueError,
            (
                "OpenAI doit proposer "
                "exactement cinq idées."
            ),
        ):
            ProductIdeaGenerationService.generate()

        self.assertEqual(
            ProductIdea.objects.count(),
            0,
        )