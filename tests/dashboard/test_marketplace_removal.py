from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.models import (
    Group,
)
from django.test import TestCase
from django.urls import (
    NoReverseMatch,
    reverse,
)
from product_intelligence.models import (
    ProductIdea,
)


class MarketplaceRemovalViewTests(TestCase):

    def test_selected_idea_no_longer_displays_marketplace_actions(
        self,
    ):
        group = Group.objects.create(
            name="Emma Operators"
        )

        user = (
            get_user_model()
            .objects.create_user(
                username="emma_without_marketplace",
                password="test-password",
            )
        )

        user.groups.add(
            group
        )

        ProductIdea.objects.create(
            name="Accessoires ergonomiques",
            customer_problem=(
                "Améliorer le confort de travail."
            ),
            target_customer=(
                "Télétravailleurs."
            ),
            reason_to_study=(
                "Besoin documenté."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "accessoire bureau ergonomique",
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

        self.assertNotContains(
            response,
            "Marketplaces à étudier",
        )

        self.assertNotContains(
            response,
            "Préparer l’étude",
        )

        self.assertNotContains(
            response,
            'name="marketplaces"',
            html=False,
        )

    def test_marketplace_routes_are_no_longer_available(
        self,
    ):
        route_names = [
            "dashboard:prepare_marketplace_study",
            "dashboard:run_marketplace_study",
        ]

        for route_name in route_names:
            with self.subTest(
                route_name=route_name,
            ):
                with self.assertRaises(
                    NoReverseMatch
                ):
                    reverse(
                        route_name,
                        args=[
                            1,
                        ],
                    )