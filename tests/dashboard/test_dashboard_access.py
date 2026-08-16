from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class DashboardAccessTests(TestCase):

    def test_emma_operator_can_access_dashboard_without_staff_status(self):
        group = Group.objects.create(
            name="Emma Operators",
        )

        user = User.objects.create_user(
            username="emma_operator",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        user.groups.add(group)

        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_staff_user_can_access_dashboard(self):
        user = User.objects.create_user(
            username="admin_test",
            password="test-password",
            is_staff=True,
            is_superuser=False,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )


    def test_regular_customer_is_redirected_to_product_list(self):
        user = User.objects.create_user(
            username="customer",
            password="test-password",
            is_staff=False,
            is_superuser=False,
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertRedirects(
            response,
            reverse("products:product_list"),
        )