from django.test import SimpleTestCase

from product_intelligence.services.product_idea_discovery import (
    ProductDiscoveryResponse,
    ProductIdeaDiscoveryService,
)


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
    ):
        self.received_instructions = (
            instructions
        )

        self.received_context = context

        self.received_response_model = (
            response_model
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
            "hypothèses",
            client.received_instructions,
        )
