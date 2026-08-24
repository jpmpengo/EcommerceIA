from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import Group

from unittest.mock import patch

from product_intelligence.models import (
    MarketplaceStudy,
    MarketObservation,
    ProductIdea,
)


class ProductIdeaViewTests(TestCase):

    def test_ordinary_customer_cannot_access_product_ideas(
        self,
    ):
        user = (
            get_user_model()
            .objects.create_user(
                username="customer",
                password="test-password",
            )
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:product_idea_list"
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            reverse(
                "products:product_list"
            ),
        )

    def test_emma_operator_can_view_proposed_product_ideas(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name=(
                "Organisateur modulable "
                "sous évier"
            ),
            customer_problem=(
                "Le rangement sous évier "
                "est difficile."
            ),
            target_customer=(
                "Habitants de petits logements."
            ),
            reason_to_study=(
                "Le besoin est concret "
                "et fréquent."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
            ],
            status="proposed",
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:product_idea_list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/product_idea_list.html",
        )

        self.assertIn(
            idea,
            response.context[
                "product_ideas"
            ],
        )

        self.assertContains(
            response,
            idea.name,
        )

    def test_emma_operator_can_select_product_idea(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator_select",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name="Organisateur de coffre",
            customer_problem=(
                "Les objets se déplacent "
                "pendant les trajets."
            ),
            target_customer=(
                "Familles utilisant une voiture."
            ),
            reason_to_study=(
                "Le besoin est fréquent."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur coffre voiture",
            ],
            status="proposed",
        )

        self.client.force_login(
            user
        )

        response = self.client.post(
            reverse(
                "dashboard:select_product_idea",
                args=[
                    idea.pk,
                ],
            )
        )

        idea.refresh_from_db()

        self.assertEqual(
            idea.status,
            "selected",
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

    def test_fourth_product_idea_selection_is_refused_cleanly(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator_limit",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        for number in range(3):
            ProductIdea.objects.create(
                name=f"Idée sélectionnée {number}",
                customer_problem="Problème client.",
                target_customer="Client cible.",
                reason_to_study="Raison.",
                countries=[
                    "FR",
                ],
                search_keywords=[
                    "mot-clé",
                ],
                status="selected",
            )

        fourth_idea = ProductIdea.objects.create(
            name="Quatrième idée",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "quatrième idée",
            ],
            status="proposed",
        )

        self.client.force_login(
            user
        )

        response = self.client.post(
            reverse(
                "dashboard:select_product_idea",
                args=[
                    fourth_idea.pk,
                ],
            )
        )

        fourth_idea.refresh_from_db()

        self.assertEqual(
            fourth_idea.status,
            "proposed",
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

    def test_emma_operator_can_reject_product_idea(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator_reject",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name="Idée non retenue",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "idée non retenue",
            ],
            status="proposed",
        )

        self.client.force_login(
            user
        )

        response = self.client.post(
            reverse(
                "dashboard:reject_product_idea",
                args=[
                    idea.pk,
                ],
            )
        )

        idea.refresh_from_db()

        self.assertEqual(
            idea.status,
            "rejected",
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

    def test_selected_product_ideas_remain_visible(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator_selected",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        selected_idea = ProductIdea.objects.create(
            name="Idée retenue pour étude",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "idée retenue",
            ],
            status="selected",
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:product_idea_list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            selected_idea,
            response.context[
                "selected_ideas"
            ],
        )

        self.assertContains(
            response,
            selected_idea.name,
        )

        self.assertContains(
            response,
            "Idées retenues pour étude",
        )

    def test_pilotage_contains_product_ideas_link(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator_navigation",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:home"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            (
                'href="'
                + reverse(
                    "dashboard:product_idea_list"
                )
                + '"'
            ),
            html=False,
        )

        self.assertContains(
            response,
            "Idées de produits",
        )

    def test_emma_operator_can_prepare_marketplace_study(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_marketplace_operator",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
                "rangement sous évier cuisine",
            ],
            status="selected",
        )

        self.client.force_login(
            user
        )

        response = self.client.post(
            reverse(
                "dashboard:prepare_marketplace_study",
                args=[
                    idea.pk,
                ],
            ),
            {
                "marketplaces": [
                    "etsy",
                ],
            },
        )

        study = MarketplaceStudy.objects.get(
            product_idea=idea
        )

        self.assertEqual(
            study.status,
            "draft",
        )

        self.assertEqual(
            study.marketplaces,
            [
                "etsy",
            ],
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

    def test_selected_idea_displays_prepared_study(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_study_viewer",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
            ],
            status="selected",
        )

        MarketplaceStudy.objects.create(
            product_idea=idea,
            marketplaces=[
                "etsy",
            ],
            queries=[
                "organisateur sous évier",
            ],
            status="draft",
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:product_idea_list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Étude préparée",
        )

        self.assertContains(
            response,
            "Etsy",
        )

        self.assertNotContains(
            response,
            "Catalogue local",
        )

        self.assertNotContains(
            response,
            "Amazon",
        )

        self.assertContains(
            response,
            "Aucun appel externe effectué",
        )

        self.assertContains(
            response,
            "Lancer l’étude",
        )

        self.assertContains(
            response,
            reverse(
                "dashboard:run_marketplace_study",
                args=[
                    idea.marketplace_studies.get().pk,
                ],
            ),
        )

    @patch(
        (
            "dashboard.views."
            "MarketplaceStudyRunner.run"
        )
    )
    def test_emma_operator_can_launch_marketplace_study(
        self,
        mock_run,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_study_runner",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
            ],
            search_keywords=[
                "organisateur sous évier",
            ],
            status="selected",
        )

        study = MarketplaceStudy.objects.create(
            product_idea=idea,
            marketplaces=[
                "etsy",
            ],
            queries=[
                "organisateur sous évier",
            ],
            status="draft",
        )

        mock_run.return_value = study

        self.client.force_login(
            user
        )

        response = self.client.post(
            reverse(
                "dashboard:run_marketplace_study",
                args=[
                    study.pk,
                ],
            ),
            follow=True,
        )

        mock_run.assert_called_once_with(
            study
        )

        self.assertRedirects(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

        self.assertContains(
            response,
            "L’étude marketplace est terminée.",
        )

    def test_completed_study_displays_observation_count(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_completed_study",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
            ],
            search_keywords=[
                "organisateur sous évier",
            ],
            status="selected",
        )

        study = MarketplaceStudy.objects.create(
            product_idea=idea,
            marketplaces=[
                "etsy",
            ],
            queries=[
                "organisateur sous évier",
            ],
            status="completed",
        )

        observations = [
            MarketObservation.objects.create(
                source="etsy",
                external_id="ETSY-001",
                name="Organisateur Etsy",
                observed_price="29.90",
                currency="EUR",
            ),
            MarketObservation.objects.create(
                source="etsy",
                external_id="ETSY-002",
                name="Organisateur Etsy alternatif",
                observed_price="24.90",
                currency="EUR",
            ),
        ]

        study.observations.add(
            *observations
        )

        self.client.force_login(
            user
        )

        response = self.client.get(
            reverse(
                "dashboard:product_idea_list"
            )
        )

        self.assertContains(
            response,
            "Étude terminée",
        )

        self.assertContains(
            response,
            "2 observations collectées",
        )

        self.assertNotContains(
            response,
            "Lancer l’étude",
        )