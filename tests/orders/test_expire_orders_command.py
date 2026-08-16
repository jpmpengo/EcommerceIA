from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from orders.models import Order


User = get_user_model()


class ExpireOrdersCommandTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_test",
            password="test12345",
        )

    def test_command_expires_outdated_pending_order(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="pending",
            paid=False,
            reservation_expires_at=(
                timezone.now()
                - timedelta(minutes=1)
            ),
        )

        call_command(
            "expire_orders"
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "expired",
        )

        self.assertFalse(
            order.paid
        )

        