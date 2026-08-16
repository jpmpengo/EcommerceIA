from django.test import TestCase

from dashboard.services.emma_state_service import (
    EmmaState,
    EmmaStateService,
)


class EmmaStateServiceTests(TestCase):

    def test_returns_action_required_when_priority_exists(
        self,
    ):
        state = EmmaStateService.get_state(
            progress=[],
            priority={"title": "Publier"},
            alerts=[],
            preparation=[],
        )

        self.assertEqual(
            state,
            EmmaState.ACTION_REQUIRED,
        )

    def test_returns_all_clear_when_no_priority(
        self,
    ):
        state = EmmaStateService.get_state(
            progress=[],
            priority=None,
            alerts=[],
            preparation=[],
        )

        self.assertEqual(
            state,
            EmmaState.ALL_CLEAR,
        )
    
    def test_returns_preparation_required_when_items_exist(self):
        state = EmmaStateService.get_state(
            progress=[],
            priority=None,
            alerts=[],
            preparation=[
                {
                    "title": "Souris Logitech MX",
                }
            ],
        )

        self.assertEqual(
            state,
            EmmaState.PREPARATION_REQUIRED,
        )

        