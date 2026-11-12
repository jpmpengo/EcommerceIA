from django.test import TestCase

from dashboard.services.emma_state_service import EmmaState
from dashboard.services.emma_summary_service import (
    EmmaSummaryService,
)


class EmmaSummaryServiceTests(TestCase):

    def test_returns_summary_when_opportunities_wait_for_review(self):
        summary = EmmaSummaryService.build(
            EmmaState.REVIEW_REQUIRED
        )

        self.assertEqual(
            summary["title"],
            "Des opportunites sont pretes a etre examinees",
        )

        self.assertIn(
            "assistants",
            summary["message"],
        )

    def test_returns_summary_when_no_opportunity_waits_for_review(self):
        summary = EmmaSummaryService.build(
            EmmaState.ALL_CLEAR
        )

        self.assertEqual(
            summary["title"],
            "Aucune opportunite a examiner",
        )

        self.assertIn(
            "opportunite",
            summary["message"],
        )
