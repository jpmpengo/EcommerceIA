from django.contrib.auth import get_user_model
from django.test import TestCase

from dashboard.models import EmmaMemory
from dashboard.services.emma_memory_service import (
    EmmaMemoryService,
)


class EmmaMemoryServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="commercant",
            password="mot-de-passe-test",
        )

    def test_get_creates_memory_when_missing(self):
        memory = EmmaMemoryService.get(self.user)

        self.assertIsInstance(
            memory,
            EmmaMemory,
        )

        self.assertEqual(
            memory.user,
            self.user,
        )

    def test_last_visit_is_none_on_first_visit(self):
        last_visit = EmmaMemoryService.last_visit(
            self.user
        )

        self.assertIsNone(last_visit)

    def test_record_visit_updates_last_visit(self):
        previous_visit = EmmaMemoryService.record_visit(
            self.user
        )

        memory = EmmaMemoryService.get(self.user)
        memory.refresh_from_db()

        self.assertIsNone(previous_visit)
        self.assertIsNotNone(memory.last_visit)

    def test_record_visit_returns_previous_visit(self):
        EmmaMemoryService.record_visit(self.user)

        first_visit = EmmaMemoryService.last_visit(
            self.user
        )

        previous_visit = EmmaMemoryService.record_visit(
            self.user
        )

        self.assertEqual(
            previous_visit,
            first_visit,
        )

        