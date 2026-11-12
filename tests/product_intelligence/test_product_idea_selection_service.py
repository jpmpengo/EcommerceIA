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


        self.assertEqual(
            idea.selection_source,
            "manual",
        )

    def test_select_can_mark_selection_as_automatic(self):
        idea = ProductIdea.objects.create(
            name="Idee automatique",
            customer_problem="Probleme client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=["FR", "BE", "ES"],
        )

        ProductIdeaSelectionService.select(
            idea,
            selection_source="automatic",
        )

        idea.refresh_from_db()

        self.assertEqual(
            idea.status,
            "selected",
        )
        self.assertEqual(
            idea.selection_source,
            "automatic",
        )

    def test_select_rejects_invalid_selection_source(self):
        idea = ProductIdea.objects.create(
            name="Idee source invalide",
            customer_problem="Probleme client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=["FR"],
        )

        with self.assertRaisesMessage(
            ValueError,
            "Origine de selection invalide.",
        ):
            ProductIdeaSelectionService.select(
                idea,
                selection_source="unknown",
            )

    def test_select_preserves_original_selection_source(self):
        idea = ProductIdea.objects.create(
            name="Idee deja selectionnee",
            customer_problem="Probleme client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=["FR"],
        )

        ProductIdeaSelectionService.select(
            idea,
            selection_source="manual",
        )
        ProductIdeaSelectionService.select(
            idea,
            selection_source="automatic",
        )

        idea.refresh_from_db()

        self.assertEqual(
            idea.selection_source,
            "manual",
        )

    def test_select_rejects_sixth_selected_idea(
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
                7,
            )
        ]

        for idea in ideas[:5]:
            (
                ProductIdeaSelectionService
                .select(
                    idea
                )
            )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Cinq idées sont déjà "
                "sélectionnées."
            ),
        ):
            (
                ProductIdeaSelectionService
                .select(
                    ideas[5]
                )
            )

        ideas[5].refresh_from_db()

        self.assertEqual(
            ideas[5].status,
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
