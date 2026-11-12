from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


class RunNightlyProductIdeasCommandTests(TestCase):

    @patch(
        "product_intelligence.management.commands.run_nightly_product_ideas.ProductIdeaNightlyOrchestratorService.run"
    )
    def test_command_runs_nightly_orchestrator_and_displays_summary(self, mock_run):
        mock_run.return_value = {
            "succeeded_ids": [57, 59],
            "failed_ids": [60],
            "failures": [
                {
                    "product_idea_id": 60,
                    "stage": "analysis",
                    "error": "Erreur technique",
                }
            ],
        }

        output = StringIO()

        call_command(
            "run_nightly_product_ideas",
            stdout=output,
        )

        mock_run.assert_called_once_with()
        text = output.getvalue()
        self.assertIn("57", text)
        self.assertIn("59", text)
        self.assertIn("60", text)
        self.assertIn("analysis", text)

    @patch("product_intelligence.management.commands.run_nightly_product_ideas.ProductIdeaNightlyOrchestratorService.run")
    def test_command_can_run_only_one_idea(self, mock_run):
        mock_run.return_value = {"succeeded_ids": [57], "failed_ids": [], "failures": []}
        output = StringIO()
        call_command("run_nightly_product_ideas", idea_id=57, stdout=output)
        mock_run.assert_called_once_with(idea_id=57)
