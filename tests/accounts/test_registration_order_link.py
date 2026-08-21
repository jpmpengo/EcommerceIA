from django.test import TestCase
from django.urls import reverse

from orders.models import Order

from django.contrib.auth import (
    get_user_model,
)


class RegistrationOrderLinkTests(TestCase):

    def test_registration_prefills_email_from_guest_order(
        self,
    ):
        order = Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email="client@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        session = self.client.session

        session["guest_order_ids"] = [
            order.id,
        ]

        session.save()

        response = self.client.get(
            reverse(
                "accounts:register"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                "form"
            ].initial["email"],
            order.email,
        )

        self.assertEqual(
            response.context[
                "form"
            ].initial["first_name"],
            order.first_name,
        )

        self.assertEqual(
            response.context[
                "form"
            ].initial["last_name"],
            order.last_name,
        )

        self.assertContains(
            response,
            (
                'value="client@example.com"'
            ),
        )

    def test_registration_links_matching_guest_order_to_account(
        self,
    ):
        order = Order.objects.create(
            first_name="Jean",
            last_name="Test",
            email="client@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        session = self.client.session

        session["guest_order_ids"] = [
            order.id,
        ]

        session.save()

        response = self.client.post(
            reverse(
                "accounts:register"
            ),
            {
                "username": "client_test",
                "first_name": "Jean",
                "last_name": "Test",
                "email": "client@example.com",
                "password1": (
                    "MotDePasse-Test-2026!"
                ),
                "password2": (
                    "MotDePasse-Test-2026!"
                ),
            },
        )

        user = (
            get_user_model()
            .objects.get(
                username="client_test"
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            order.user,
            user,
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_list"
            ),
        )

        self.assertNotIn(
            "guest_order_ids",
            self.client.session,
        )

    def test_registration_rejects_email_already_used_by_account(
        self,
    ):
        User = get_user_model()

        User.objects.create_user(
            username="existing_client",
            email="Client@Example.com",
            password=(
                "MotDePasse-Existant-2026!"
            ),
        )

        response = self.client.post(
            reverse(
                "accounts:register"
            ),
            {
                "username": "new_client",
                "first_name": "Jean",
                "last_name": "Test",
                "email": "client@example.com",
                "password1": (
                    "MotDePasse-Test-2026!"
                ),
                "password2": (
                    "MotDePasse-Test-2026!"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            (
                "Un compte utilise déjà "
                "cette adresse e-mail."
            ),
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

        self.assertFalse(
            response.wsgi_request
            .user
            .is_authenticated
        )

    def test_registration_does_not_link_order_with_different_email(
        self,
    ):
        order = Order.objects.create(
            first_name="Autre",
            last_name="Client",
            email="other@example.com",
            phone="0102030405",
            address="2 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=True,
            status="paid",
        )

        session = self.client.session

        session["guest_order_ids"] = [
            order.id,
        ]

        session.save()

        self.client.post(
            reverse(
                "accounts:register"
            ),
            {
                "username": "client_test",
                "first_name": "Jean",
                "last_name": "Test",
                "email": "client@example.com",
                "password1": (
                    "MotDePasse-Test-2026!"
                ),
                "password2": (
                    "MotDePasse-Test-2026!"
                ),
            },
        )

        order.refresh_from_db()

        self.assertIsNone(
            order.user
        )

        self.assertIn(
            order.id,
            self.client.session[
                "guest_order_ids"
            ],
        )
