from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)
from product_intelligence.services.product_idea_selection import (
    ProductIdeaSelectionService,
)


class ProductIdeaSelectionServiceTests(
    TestCase
):

    def test_select_marks_proposed_idea_as_selected(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem=(
                "Le rangement est difficile."
            ),
            target_customer=(
                "Habitants de petits logements."
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
                "organisateur sous évier",
            ],
            source="openai",
            model_name="gpt-5.6-luna",
        )

        ProductIdeaSelectionService.select(
            idea
        )

        idea.refresh_from_db()

        self.assertEqual(
            idea.status,
            "selected",
        )

    def test_select_rejects_fourth_selected_idea(
        self,
    ):
        ideas = [
            ProductIdea.objects.create(
                name=(
                    f"Idée produit {index}"
                ),
                customer_problem=(
                    "Problème client."
                ),
                target_customer=(
                    "Client cible."
                ),
                reason_to_study=(
                    "Hypothèse à vérifier."
                ),
                countries=[
                    "FR",
                    "BE",
                    "ES",
                ],
                search_keywords=[
                    f"produit {index}",
                ],
                source="openai",
                model_name="gpt-5.6-luna",
            )
            for index in range(
                1,
                5,
            )
        ]

        for idea in ideas[:3]:
            (
                ProductIdeaSelectionService
                .select(
                    idea
                )
            )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Trois idées sont déjà "
                "sélectionnées."
            ),
        ):
            (
                ProductIdeaSelectionService
                .select(
                    ideas[3]
                )
            )

        ideas[3].refresh_from_db()

        self.assertEqual(
            ideas[3].status,
            "proposed",
        )

    def test_reject_marks_proposed_idea_as_rejected(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Idée à écarter",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "idée à écarter",
            ],
            status="proposed",
        )

        rejected_idea = (
            ProductIdeaSelectionService
            .reject(
                idea
            )
        )

        idea.refresh_from_db()

        self.assertEqual(
            idea.status,
            "rejected",
        )

        self.assertEqual(
            rejected_idea.status,
            "rejected",
        )