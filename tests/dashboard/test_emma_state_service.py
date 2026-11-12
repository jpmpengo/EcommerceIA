from django.test import TestCase

from dashboard.services.emma_state_service import (
    EmmaState,
    EmmaStateService,
)


class EmmaStateServiceTests(TestCase):

    def test_returns_review_required_when_opportunities_wait_for_review(self):
        state = EmmaStateService.get_state(
            review_opportunities_count=2,
        )

        self.assertEqual(
            state,
            EmmaState.REVIEW_REQUIRED,
        )

    def test_returns_all_clear_when_no_opportunity_waits_for_review(self):
        state = EmmaStateService.get_state(
            review_opportunities_count=0,
        )

        self.assertEqual(
            state,
            EmmaState.ALL_CLEAR,
        )
