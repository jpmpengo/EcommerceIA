from django.test import TestCase

from dashboard.services.emma_state_service import EmmaState
from dashboard.services.emma_summary_service import (
    EmmaSummaryService,
)


class EmmaSummaryServiceTests(TestCase):

    def test_returns_summary_for_action_required(self):
        summary = EmmaSummaryService.build(
            EmmaState.ACTION_REQUIRED
        )

        self.assertEqual(
            summary["title"],
            "Votre attention est requise",
        )

        self.assertIn(
            "conseille",
            summary["message"],
        )

    def test_returns_summary_for_all_clear(self):
        summary = EmmaSummaryService.build(
            EmmaState.ALL_CLEAR
        )

        self.assertEqual(
            summary["title"],
            "Tout est sous contrôle",
        )

        self.assertIn(
            "traitées",
            summary["message"],
        )

        