from io import StringIO
from unittest.mock import patch

from django.core.management import (
    CommandError,
    call_command,
)
from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)


class CollectComparablePricesCommandTests(
    TestCase
):

    def setUp(self):
        self.product_idea = (
            ProductIdea.objects.create(
                name=(
                    "Rangements modulaires"
                ),
                customer_problem=(
                    "Manque de place."
                ),
                target_customer=(
                    "Habitants de petits logements."
                ),
                reason_to_study=(
                    "Besoin concret."
                ),
                countries=[
                    "FR",
                    "BE",
                    "ES",
                ],
                search_keywords=[
                    "rangement gain de place",
                ],
                supplier_search_keywords=[
                    "space saving storage organizer",
                ],
                status="selected",
            )
        )

    @patch(
        (
            "product_intelligence.management."
            "commands.collect_comparable_prices."
            "ComparablePriceRunnerFactory.build"
        )
    )
    def test_collects_comparable_prices_for_product_idea(
        self,
        build_runner,
    ):
        runner = build_runner.return_value

        runner.run.return_value = {
            "offers_processed": 5,
            "comparable_prices_saved": 18,
        }

        output = StringIO()

        call_command(
            "collect_comparable_prices",
            self.product_idea.pk,
            stdout=output,
        )

        build_runner.assert_called_once_with(
            model=None,
        )

        runner.run.assert_called_once_with(
            product_idea=(
                self.product_idea
            ),
        )

        command_output = output.getvalue()

        self.assertIn(
            "5 offre(s) fournisseur traitée(s)",
            command_output,
        )

        self.assertIn(
            "18 prix comparable(s) enregistré(s)",
            command_output,
        )

    @patch(
        (
            "product_intelligence.management."
            "commands.collect_comparable_prices."
            "ComparablePriceRunnerFactory.build"
        )
    )
    def test_accepts_custom_model(
        self,
        build_runner,
    ):
        runner = build_runner.return_value

        runner.run.return_value = {
            "offers_processed": 0,
            "comparable_prices_saved": 0,
        }

        call_command(
            "collect_comparable_prices",
            self.product_idea.pk,
            model="test-model",
            stdout=StringIO(),
        )

        build_runner.assert_called_once_with(
            model="test-model",
        )

    def test_rejects_unknown_product_idea(
        self,
    ):
        with self.assertRaisesMessage(
            CommandError,
            "Idée produit introuvable.",
        ):
            call_command(
                "collect_comparable_prices",
                999999,
                stdout=StringIO(),
            )