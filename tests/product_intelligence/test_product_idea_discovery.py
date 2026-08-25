from django.test import SimpleTestCase

from product_intelligence.services.product_idea_discovery import (
    ProductDiscoveryResponse,
    ProductIdeaDiscoveryService,
)

from pydantic import ValidationError


class FakeDiscoveryClient:

    def __init__(self):
        self.received_instructions = None
        self.received_context = None
        self.received_response_model = None

    def generate(
        self,
        instructions,
        context,
        response_model,
        use_web_search=False,
    ):
        self.received_instructions = (
            instructions
        )

        self.received_context = context

        self.received_response_model = (
            response_model
        )
        self.received_use_web_search = (
            use_web_search
        )

        return {
            "ideas": [
                {
                    "name": (
                        f"Produit test {index}"
                    ),
                    "customer_problem": (
                        "Problème client à vérifier."
                    ),
                    "target_customer": (
                        "Client européen."
                    ),
                    "reason_to_study": (
                        "Hypothèse commerciale "
                        "à valider."
                    ),
                    "countries": [
                        "FR",
                        "BE",
                        "ES",
                    ],
                    "search_keywords": [
                        "produit test",
                    ],
                }
                for index in range(
                    1,
                    6,
                )
            ],
        }


class ProductIdeaDiscoveryServiceTests(
    SimpleTestCase
):

    def test_requests_exactly_five_ideas_for_initial_markets(
        self,
    ):
        client = FakeDiscoveryClient()

        service = (
            ProductIdeaDiscoveryService(
                client=client
            )
        )

        result = service.discover()

        self.assertEqual(
            client.received_context[
                "maximum_ideas"
            ],
            5,
        )

        self.assertEqual(
            client.received_context[
                "target_countries"
            ],
            [
                "FR",
                "BE",
                "ES",
            ],
        )

        self.assertEqual(
            client.received_response_model,
            ProductDiscoveryResponse,
        )

        self.assertEqual(
            len(result["ideas"]),
            5,
        )

        self.assertIn(
            "catégories",
            client.received_instructions,
        )

        self.assertIn(
            "sources",
            client.received_instructions,
        )

        self.assertIn(
            "signaux de demande",
            client.received_instructions,
        )

        self.assertNotIn(
            "marketplace",
            (
                client.received_instructions
                .lower()
            ),
        )

        self.assertTrue(
            client.received_use_web_search
        )

    def test_response_rejects_categories_without_demand_evidence(
        self,
    ):
        categories = [
            {
                "name": (
                    f"Catégorie test {index}"
                ),
                "customer_problem": (
                    "Problème client."
                ),
                "target_customer": (
                    "Client européen."
                ),
                "reason_to_study": (
                    "Catégorie à vérifier."
                ),
                "countries": [
                    "FR",
                ],
                "search_keywords": [
                    "catégorie test",
                ],
            }
            for index in range(
                1,
                6,
            )
        ]

        with self.assertRaises(
            ValidationError
        ):
            ProductDiscoveryResponse.model_validate(
                {
                    "ideas": categories,
                }
            )
