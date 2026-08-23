from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)


class ProductIdeaModelTests(TestCase):

    def test_product_idea_is_stored_as_unvalidated_hypothesis(
        self,
    ):
        idea = ProductIdea.objects.create(
            name=(
                "Organisateur modulaire "
                "pour coffre"
            ),
            customer_problem=(
                "Les objets se déplacent "
                "pendant les trajets."
            ),
            target_customer=(
                "Familles et conducteurs."
            ),
            reason_to_study=(
                "Besoin concret à vérifier."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                (
                    "organisateur coffre "
                    "voiture pliable"
                ),
            ],
            source="openai",
            model_name="gpt-5.6-luna",
        )

        self.assertEqual(
            idea.status,
            "proposed",
        )

        self.assertEqual(
            idea.countries,
            [
                "FR",
                "BE",
                "ES",
            ],
        )

        self.assertFalse(
            idea.is_validated
        )

        self.assertIsNotNone(
            idea.created_at
        )
