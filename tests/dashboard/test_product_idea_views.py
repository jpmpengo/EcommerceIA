from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import Group

from unittest.mock import patch

from product_intelligence.models import (
    ProductIdea,
)

class ProductIdeaViewTests(TestCase):

    def create_operator(self, username):
        group, unused = Group.objects.get_or_create(
            name="Emma Operators"
        )
        user = get_user_model().objects.create_user(
            username=username,
            password="test-password",
        )
        user.groups.add(group)
        return user

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
            demand_signals=[
                (
                    "Les recherches publiques "
                    "montrent un intérêt pour "
                    "le rangement compact."
                ),
            ],
            evidence_sources=[
                {
                    "title": (
                        "Étude sur le rangement "
                        "des petits logements"
                    ),
                    "url": (
                        "https://example.com/"
                        "rangement-compact"
                    ),
                    "evidence": (
                        "La source décrit une "
                        "demande pour des solutions "
                        "de rangement compactes."
                    ),
                },
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

        self.assertContains(
            response,
            "Signaux de demande",
        )

        self.assertContains(
            response,
            (
                "Les recherches publiques "
                "montrent un intérêt pour "
                "le rangement compact."
            ),
        )

        self.assertContains(
            response,
            "Sources consultées",
        )

        self.assertContains(
            response,
            (
                "Étude sur le rangement "
                "des petits logements"
            ),
        )

        self.assertContains(
            response,
            (
                'href="https://example.com/'
                'rangement-compact"'
            ),
            html=False,
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

    def test_sixth_product_idea_selection_is_refused_cleanly(
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

        for number in range(5):
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

        sixth_idea = ProductIdea.objects.create(
            name="Sixième idée",
            customer_problem="Problème client.",
            target_customer="Client cible.",
            reason_to_study="Raison.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "sixième idée",
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
                    sixth_idea.pk,
                ],
            )
        )

        sixth_idea.refresh_from_db()

        self.assertEqual(
            sixth_idea.status,
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

        self.assertContains(
            response,
            "Lancer l’étude",
        )

        self.assertContains(
            response,
            "Étude en cours",
        )

        self.assertContains(
            response,
            "analysis-wait-time",
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
                "dashboard:product_idea_list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Pilotage",
        )

        self.assertContains(
            response,
            "Idées de produits",
        )

    @patch(
        "dashboard.views.ProductIdeaManualAnalysisService.run"
    )
    def test_operator_can_launch_selected_idea_analysis(
        self,
        run_analysis,
    ):
        user = self.create_operator("manual_analysis")
        idea = ProductIdea.objects.create(
            name="Idée à étudier",
            customer_problem="Problème.",
            target_customer="Client.",
            reason_to_study="Raison.",
            countries=["FR"],
            status="selected",
        )
        run_analysis.return_value = {
            "offers_analyzed": 3,
            "opportunities_created": 1,
        }
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "dashboard:analyze_product_idea",
                args=[idea.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard:product_idea_list"),
        )
        run_analysis.assert_called_once_with(
            product_idea=idea
        )

    @patch(
        "dashboard.views.ProductIdeaManualAnalysisService.run"
    )
    def test_customer_cannot_launch_idea_analysis(
        self,
        run_analysis,
    ):
        user = get_user_model().objects.create_user(
            username="customer_analysis",
            password="test-password",
        )
        idea = ProductIdea.objects.create(
            name="Idée protégée",
            customer_problem="Problème.",
            target_customer="Client.",
            reason_to_study="Raison.",
            countries=["FR"],
            status="selected",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "dashboard:analyze_product_idea",
                args=[idea.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("products:product_list"),
        )
        run_analysis.assert_not_called()

    @patch(
        (
            "dashboard.views."
            "ProductIdeaGenerationService.generate"
        )
    )
    def test_emma_operator_can_generate_product_ideas(
        self,
        mock_generate,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_idea_generator",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        self.client.force_login(
            user
        )

        mock_generate.return_value = 5

        response = self.client.post(
            reverse(
                "dashboard:generate_product_ideas"
            )
        )

        mock_generate.assert_called_once_with()

        self.assertRedirects(
            response,
            reverse(
                "dashboard:product_idea_list"
            ),
        )

    def test_product_idea_page_displays_generation_action(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_generation_action",
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
                "dashboard:product_idea_list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Générer de nouvelles idées",
        )

        self.assertContains(
            response,
            reverse(
                "dashboard:generate_product_ideas"
            ),
        )

    @patch(
        (
            "dashboard.views."
            "ProductIdeaGenerationService.generate"
        )
    )
    def test_generation_displays_business_error(
        self,
        mock_generate,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_generation_guard",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        self.client.force_login(
            user
        )

        mock_generate.side_effect = ValueError(
            (
                "Des idées sont déjà "
                "en attente d’examen."
            )
        )

        response = self.client.post(
            reverse(
                "dashboard:generate_product_ideas"
            ),
            follow=True,
        )

        self.assertContains(
            response,
            (
                "Des idées sont déjà "
                "en attente d’examen."
            ),
        )

    def test_generation_action_is_hidden_when_proposed_ideas_exist(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_existing_ideas",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

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

        self.assertNotContains(
            response,
            "Générer de nouvelles idées",
        )
