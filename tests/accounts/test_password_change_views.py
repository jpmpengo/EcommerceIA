from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.urls import reverse


class PasswordChangeViewTests(TestCase):

    def setUp(self):
        self.user = (
            get_user_model()
            .objects.create_user(
                username="client_test",
                email="client@example.com",
                password=(
                    "Ancien-MotDePasse-2026!"
                ),
            )
        )

        self.client.login(
            username="client_test",
            password=(
                "Ancien-MotDePasse-2026!"
            ),
        )

    def test_authenticated_user_can_open_password_change_page(
        self,
    ):
        response = self.client.get(
            reverse(
                "password_change"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            (
                "registration/"
                "password_change_form.html"
            ),
        )

        self.assertContains(
            response,
            "Modifier mon mot de passe",
        )

    def test_user_can_change_password(
        self,
    ):
        response = self.client.post(
            reverse(
                "password_change"
            ),
            {
                "old_password": (
                    "Ancien-MotDePasse-2026!"
                ),
                "new_password1": (
                    "Nouveau-MotDePasse-2026!"
                ),
                "new_password2": (
                    "Nouveau-MotDePasse-2026!"
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "password_change_done"
            ),
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.check_password(
                "Ancien-MotDePasse-2026!"
            )
        )

        self.assertTrue(
            self.user.check_password(
                "Nouveau-MotDePasse-2026!"
            )
        )

        self.assertTrue(
            response.wsgi_request
            .user
            .is_authenticated
        )

    def test_authenticated_user_sees_password_change_link(
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
                "password_change"
            ),
        )

        self.assertContains(
            response,
            "Modifier mon mot de passe",
        )
