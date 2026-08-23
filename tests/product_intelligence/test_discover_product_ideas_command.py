from io import StringIO
from unittest.mock import (
    Mock,
    patch,
)

from django.core.management import (
    call_command,
)

from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)

class DiscoverProductIdeasCommandTests(
    TestCase
):

    @patch(
        "product_intelligence.management."
        "commands.discover_product_ideas."
        "Command._build_service"
    )
    def test_command_prints_five_product_ideas(
        self,
        build_service,
    ):
        service = Mock()

        service.discover.return_value = {
            "ideas": [
                {
                    "name": (
                        f"Produit test {index}"
                    ),
                    "customer_problem": (
                        "Problème à vérifier"
                    ),
                    "target_customer": (
                        "Client européen"
                    ),
                    "reason_to_study": (
                        "Hypothèse à valider"
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

        build_service.return_value = (
            service
        )

        output = StringIO()

        call_command(
            "discover_product_ideas",
            model="test-model",
            stdout=output,
        )

        build_service.assert_called_once_with(
            "test-model"
        )

        service.discover.assert_called_once_with()

        rendered_output = output.getvalue()

        self.assertIn(
            "5 idée(s) proposée(s)",
            rendered_output,
        )

        self.assertIn(
            "Produit test 1",
            rendered_output,
        )

        self.assertIn(
            "Produit test 5",
            rendered_output,
        )

        self.assertEqual(
            ProductIdea.objects.count(),
            5,
        )

        first_idea = (
            ProductIdea.objects
            .order_by("id")
            .first()
        )

        self.assertEqual(
            first_idea.name,
            "Produit test 1",
        )

        self.assertEqual(
            first_idea.status,
            "proposed",
        )

        self.assertEqual(
            first_idea.model_name,
            "test-model",
        )
