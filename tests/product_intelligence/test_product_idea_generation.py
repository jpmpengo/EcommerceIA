from unittest.mock import patch

from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
    ProductIdeaVisualReference,
)
from product_intelligence.services.product_idea_generation import (
    ProductIdeaGenerationService,
)


class ProductIdeaGenerationServiceTests(
    TestCase
):

    @patch("product_intelligence.services.product_idea_generation.ProductIdeaScoreService.calculate")
    @patch.object(ProductIdeaGenerationService, "_build_discovery_service")
    def test_generation_scores_ideas_with_a_reference_date(self, mock_build, mock_score):
        from datetime import date

        mock_score.return_value = 75
        mock_build.return_value.discover.return_value = {
            "ideas": [
                {
                    "name": f"Idea {number}",
                    "customer_problem": "Problem",
                    "target_customer": "Customer",
                    "reason_to_study": "Reason",
                    "countries": ["FR"],
                    "category_path": ["Maison"],
                    "search_keywords": ["keyword"],
                    "supplier_search_keywords": ["supplier keyword"],
                    "supplier_search_keywords_localized": [{"supplier_search_keyword": "supplier keyword", "FR": "mot cle", "DE": "stichwort", "ES": "palabra"}],
                    "visual_references": [{"supplier_search_keyword": "supplier keyword", "product_name": "Product", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/image.jpg"}],
                    "demand_signals": ["Signal"],
                    "demand_signal_assessments": [{"type": "trend", "markets": ["US"], "role": "precursor", "strength": "strong", "metric": "search_trend", "value": "growth", "source_url": "https://example.com/source", "observed_at": date(2026, 9, 20)}],
                    "evidence_sources": [{"title": "Source", "url": "https://example.com/source", "evidence": "Evidence"}],
                }
                for number in range(1, 6)
            ]
        }

        ProductIdeaGenerationService.generate(model="test-model")

        self.assertIsNotNone(mock_score.call_args.kwargs.get("reference_date"))


    def test_normalizes_observed_at_date_for_json_storage(self):
        from datetime import date

        assessments = [
            {
                "type": "trend",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend",
                "value": "documented growth",
                "source_url": "https://example.com/source",
                "observed_at": date(2026, 9, 28),
            }
        ]

        normalized = ProductIdeaGenerationService._normalize_demand_signal_assessments(
            assessments
        )

        self.assertEqual(
            normalized[0]["observed_at"],
            "2026-09-28",
        )


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
            customer_problem=(
                "Problème client."
            ),
            target_customer=(
                "Client cible."
            ),
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
                    "name": (
                        f"Idée {number}"
                    ),
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
                    "supplier_search_keywords": [
                        (
                            "supplier keyword "
                            f"{number}"
                        ),
                    ],
                    "supplier_search_keywords_localized": [
                        {
                            "supplier_search_keyword": f"supplier keyword {number}",
                            "FR": f"mot fournisseur {number}",
                            "DE": f"lieferantenwort {number}",
                            "ES": f"palabra proveedor {number}",
                        }
                    ],
                    "category_path": [
                        "Maison",
                        "Organisation",
                    ],
                    "visual_references": [
                        {
                            "supplier_search_keyword": (
                                "supplier keyword "
                                f"{number}"
                            ),
                            "product_name": (
                                f"Produit visuel {number}"
                            ),
                            "source_title": (
                                f"Source visuelle {number}"
                            ),
                            "source_url": (
                                "https://example.com/"
                                f"visual-{number}"
                            ),
                            "image_url": (
                                "https://example.com/"
                                f"visual-{number}.jpg"
                            ),
                        },
                    ],
                    "demand_signals": [
                        (
                            "Signal de demande "
                            f"{number}."
                        ),
                    ],
                    "demand_signal_assessments": [
                        {
                            "type": "direct",
                            "markets": ["US", "JP"],
                            "role": "precursor",
                            "strength": "strong",
                            "metric": "sales",
                            "value": "documented purchases",
                            "source_url": "https://example.com/source-signal",
                            "observed_at": "2026-09-25",
                        },
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
            first_idea.supplier_search_keywords_localized,
            {
                "FR": {"supplier keyword 1": "mot fournisseur 1"},
                "DE": {"supplier keyword 1": "lieferantenwort 1"},
                "ES": {"supplier keyword 1": "palabra proveedor 1"},
            },
        )

        self.assertEqual(
            first_idea.supplier_search_keywords,
            [
                "supplier keyword 1",
            ],
        )

        self.assertEqual(
            first_idea.category_path,
            [
                "Maison",
                "Organisation",
            ],
        )

        self.assertEqual(
            ProductIdeaVisualReference.objects.count(),
            5,
        )

        first_reference = (
            ProductIdeaVisualReference.objects
            .order_by("id")
            .first()
        )

        self.assertEqual(
            first_reference.product_idea,
            first_idea,
        )
        self.assertEqual(
            first_reference.supplier_search_keyword,
            "supplier keyword 1",
        )
        self.assertEqual(
            first_reference.image_url,
            "https://example.com/visual-1.jpg",
        )
        self.assertEqual(
            first_reference.model_name,
            "test-model",
        )

        self.assertEqual(
            first_idea.demand_signals,
            [
                "Signal de demande 1.",
            ],
        )

        self.assertEqual(
            first_idea.idea_score,
            80,
        )

        self.assertEqual(
            first_idea.demand_signal_assessments,
            [
                {
                    "type": "direct",
                    "markets": ["US", "JP"],
                    "role": "precursor",
                    "strength": "strong",
                    "metric": "sales",
                    "value": "documented purchases",
                    "source_url": "https://example.com/source-signal",
                    "observed_at": "2026-09-25",
                },
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
                    "name": (
                        f"Idée {number}"
                    ),
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

    @patch('product_intelligence.services.product_idea_generation.ProductIdeaEvidenceVerificationService')
    def test_save_ideas_persists_rejected_sales_growth_with_zero_score(self, mock_verifier):
        mock_verifier.return_value.verify.return_value.is_verified = False
        idea = {
            'name': 'Test rejected growth', 'customer_problem': 'Problem', 'target_customer': 'Customer', 'reason_to_study': 'Reason', 'countries': ['FR'], 'category_path': ['Maison'], 'search_keywords': [], 'supplier_search_keywords': [], 'supplier_search_keywords_localized': [], 'visual_references': [], 'demand_signals': [], 'evidence_sources': [],
            'demand_signal_assessments': [{'type': 'direct', 'markets': ['US'], 'role': 'precursor', 'strength': 'strong', 'metric': 'sales_growth', 'value': 'Sales rose 149%', 'source_url': 'https://example.com/source'}],
        }
        ProductIdeaGenerationService._save_ideas([idea], 'test-model')
        saved = ProductIdea.objects.get(name='Test rejected growth')
        self.assertIs(saved.demand_signal_assessments[0]['is_verified'], False)
        self.assertEqual(saved.idea_score, 0)

    @patch('product_intelligence.services.product_idea_generation.ProductIdeaEvidenceVerificationService')
    def test_save_ideas_persists_unverified_search_trend_with_zero_score(self, mock_verifier):
        mock_verifier.return_value.verify.return_value.is_verified = False
        idea = {
            'name': 'Test unverified trend', 'customer_problem': 'Problem', 'target_customer': 'Customer', 'reason_to_study': 'Reason', 'countries': ['FR'], 'category_path': ['Maison'], 'search_keywords': [], 'supplier_search_keywords': [], 'supplier_search_keywords_localized': [], 'visual_references': [], 'demand_signals': [], 'evidence_sources': [],
            'demand_signal_assessments': [{'type': 'direct', 'markets': ['US'], 'role': 'precursor', 'strength': 'strong', 'metric': 'search_trend', 'value': 'documented growth', 'source_url': 'https://example.com/source'}],
        }
        ProductIdeaGenerationService._save_ideas([idea], 'test-model')
        saved = ProductIdea.objects.get(name='Test unverified trend')
        self.assertIs(saved.demand_signal_assessments[0]['is_verified'], False)
        self.assertEqual(saved.idea_score, 0)
