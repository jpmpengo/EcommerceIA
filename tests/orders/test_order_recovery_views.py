import re

from django.core import mail
from django.test import (
    TestCase,
    override_settings,
)
from django.urls import reverse

from orders.models import Order

from datetime import timedelta

from django.utils import timezone


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
)
class OrderRecoveryViewTests(TestCase):

    def test_guest_can_open_order_recovery_page(
        self,
    ):
        response = self.client.get(
            reverse(
                "orders:order_recovery"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "orders/order_recovery.html",
        )

        self.assertContains(
            response,
            "Retrouver mes commandes",
        )

    def test_sends_six_digit_code_to_order_email(
        self,
    ):
        email = "client@example.com"

        Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email=email,
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        response = self.client.post(
            reverse(
                "orders:order_recovery"
            ),
            {
                "email": email,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertEqual(
            mail.outbox[0].to,
            [
                email,
            ],
        )

        code_match = re.search(
            r"\b(\d{6})\b",
            mail.outbox[0].body,
        )

        self.assertIsNotNone(
            code_match
        )

    def test_valid_code_restores_orders_in_session(
        self,
    ):
        email = "client@example.com"

        order = Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email=email,
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        self.client.post(
            reverse(
                "orders:order_recovery"
            ),
            {
                "email": email,
            },
        )

        code_match = re.search(
            r"\b(\d{6})\b",
            mail.outbox[0].body,
        )

        code = code_match.group(1)

        response = self.client.post(
            reverse(
                "orders:order_recovery_verify"
            ),
            {
                "code": code,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_list"
            ),
        )

        self.assertIn(
            order.id,
            self.client.session[
                "guest_order_ids"
            ],
        )

        self.assertNotIn(
            "order_recovery",
            self.client.session,
        )

    def test_invalid_code_does_not_restore_orders(
        self,
    ):
        email = "client@example.com"

        order = Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email=email,
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        self.client.post(
            reverse(
                "orders:order_recovery"
            ),
            {
                "email": email,
            },
        )

        response = self.client.post(
            reverse(
                "orders:order_recovery_verify"
            ),
            {
                "code": "000000",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertContains(
            response,
            "Le code saisi est incorrect.",
            status_code=400,
        )

        self.assertNotIn(
            order.id,
            self.client.session.get(
                "guest_order_ids",
                [],
            ),
        )

        self.assertEqual(
            self.client.session[
                "order_recovery"
            ]["attempts"],
            1,
        )

    def test_guest_without_orders_sees_recovery_link(
        self,
    ):
        response = self.client.get(
            "/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            reverse(
                "orders:order_recovery"
            ),
        )

        self.assertContains(
            response,
            "Retrouver une commande",
        )

    def test_expired_code_does_not_restore_orders(
        self,
    ):
        email = "client@example.com"

        order = Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email=email,
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        self.client.post(
            reverse(
                "orders:order_recovery"
            ),
            {
                "email": email,
            },
        )

        code = re.search(
            r"\b(\d{6})\b",
            mail.outbox[0].body,
        ).group(1)

        session = self.client.session

        recovery = session[
            "order_recovery"
        ]

        recovery["expires_at"] = (
            timezone.now()
            - timedelta(seconds=1)
        ).isoformat()

        session[
            "order_recovery"
        ] = recovery

        session.save()

        response = self.client.post(
            reverse(
                "orders:order_recovery_verify"
            ),
            {
                "code": code,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_recovery"
            ),
        )

        self.assertNotIn(
            order.id,
            self.client.session.get(
                "guest_order_ids",
                [],
            ),
        )

        self.assertNotIn(
            "order_recovery",
            self.client.session,
        )

    def test_recovery_is_blocked_after_five_invalid_codes(
        self,
    ):
        email = "client@example.com"

        order = Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email=email,
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        self.client.post(
            reverse(
                "orders:order_recovery"
            ),
            {
                "email": email,
            },
        )

        valid_code = re.search(
            r"\b(\d{6})\b",
            mail.outbox[0].body,
        ).group(1)

        invalid_code = (
            "000000"
            if valid_code != "000000"
            else "111111"
        )

        for attempt in range(5):
            response = self.client.post(
                reverse(
                    "orders:order_recovery_verify"
                ),
                {
                    "code": invalid_code,
                },
            )

            if attempt < 4:
                self.assertEqual(
                    response.status_code,
                    400,
                )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_recovery"
            ),
        )

        self.assertNotIn(
            order.id,
            self.client.session.get(
                "guest_order_ids",
                [],
            ),
        )

        self.assertNotIn(
            "order_recovery",
            self.client.session,
        )
