from io import StringIO
from unittest.mock import patch

from django.core.management import (
    call_command,
)
from django.test import TestCase


class DiscoverProductIdeasCommandTests(
    TestCase
):

    @patch(
        (
            "product_intelligence.management."
            "commands.discover_product_ideas."
            "ProductIdeaGenerationService.generate"
        )
    )
    def test_command_generates_five_product_ideas(
        self,
        mock_generate,
    ):
        mock_generate.return_value = 5

        output = StringIO()

        call_command(
            "discover_product_ideas",
            model="test-model",
            stdout=output,
        )

        mock_generate.assert_called_once_with(
            model="test-model",
        )

        self.assertIn(
            "5 idée(s) proposée(s)",
            output.getvalue(),
        )