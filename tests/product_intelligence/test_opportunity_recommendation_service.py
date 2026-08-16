from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.opportunity_recommendation_service import (
    OpportunityRecommendationService,
)


class FakeAIEngine:

    def __init__(self):
        self.received_context = None

    def recommend(self, context):
        self.received_context = context

        return {
            "decision": "study",
            "summary": (
                "Opportunité intéressante. "
                "À étudier pour sourcing fournisseur."
            ),
        }


class InvalidAIEngine:

    def recommend(self, context):
        return {
            "summary": (
                "Réponse sans décision."
            ),
        }


class UnknownDecisionAIEngine:

    def recommend(self, context):
        return {
            "decision": "maybe",
            "summary": (
                "Cette opportunité semble intéressante."
            ),
        }


class OpportunityRecommendationServiceTests(SimpleTestCase):

    def test_service_returns_ai_recommendation(self):
        engine = FakeAIEngine()

        service = OpportunityRecommendationService(
            engine=engine
        )

        result = service.recommend(
            product_data={
                "name": "Support ordinateur portable",
                "current_price": Decimal("17.50"),
                "currency": "EUR",
            },
            score_data={
                "score": Decimal("62.06"),
                "reasons": [
                    "Baisse de prix de 12.06 %",
                ],
            },
        )

        self.assertEqual(
            result["decision"],
            "study",
        )

        self.assertEqual(
            result["summary"],
            (
                "Opportunité intéressante. "
                "À étudier pour sourcing fournisseur."
            ),
        )

    def test_service_sends_controlled_context_to_ai_engine(self):
        engine = FakeAIEngine()

        service = OpportunityRecommendationService(
            engine=engine
        )

        product_data = {
            "name": "Support ordinateur portable",
            "current_price": Decimal("17.50"),
            "currency": "EUR",
        }

        score_data = {
            "score": Decimal("62.06"),
            "reasons": [
                "Baisse de prix de 12.06 %",
            ],
        }

        service.recommend(
            product_data=product_data,
            score_data=score_data,
        )

        self.assertEqual(
            engine.received_context,
            {
                "product": product_data,
                "score": Decimal("62.06"),
                "reasons": [
                    "Baisse de prix de 12.06 %",
                ],
            },
        )

    def test_service_rejects_ai_response_without_decision(self):
        engine = InvalidAIEngine()

        service = OpportunityRecommendationService(
            engine=engine
        )

        with self.assertRaises(ValueError):
            service.recommend(
                product_data={
                    "name": "Support ordinateur portable",
                    "current_price": Decimal("17.50"),
                    "currency": "EUR",
                },
                score_data={
                    "score": Decimal("62.06"),
                    "reasons": [
                        "Baisse de prix de 12.06 %",
                    ],
                },
            )

    def test_service_rejects_unknown_decision(self):
        engine = UnknownDecisionAIEngine()

        service = OpportunityRecommendationService(
            engine=engine
        )

        with self.assertRaises(ValueError):
            service.recommend(
                product_data={
                    "name": "Support ordinateur portable",
                    "current_price": Decimal("17.50"),
                    "currency": "EUR",
                },
                score_data={
                    "score": Decimal("62.06"),
                    "reasons": [
                        "Baisse de prix de 12.06 %",
                    ],
                },
            )

