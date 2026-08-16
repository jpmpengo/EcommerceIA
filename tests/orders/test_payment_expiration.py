from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from orders.models import Order


User = get_user_model()


class PaymentExpirationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_test",
            password="test12345",
        )

        self.client.login(
            username="client_test",
            password="test12345",
        )

    def test_expired_pending_order_cannot_start_payment(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="Test",
            email="client@example.com",
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

        response = self.client.get(
            reverse(
                "orders:payment_create",
                args=[order.id],
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "expired",
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_detail",
                args=[order.id],
            ),
        )

        