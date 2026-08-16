from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order

from datetime import timedelta
from django.utils import timezone


User = get_user_model()


class OrderStatusDisplayTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_test",
            password="test12345",
        )

        self.client.login(
            username="client_test",
            password="test12345",
        )

    def test_pending_order_is_displayed_as_waiting_for_payment(self):
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
        )

        response = self.client.get(
            reverse("orders:order_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"#{order.id}",
        )

        self.assertContains(
            response,
            "En attente de paiement"
        )

    def test_paid_order_is_displayed_as_paid(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="paid",
            paid=True,
        )

        response = self.client.get(
            reverse("orders:order_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"#{order.id}",
        )

        self.assertContains(
            response,
            "Payée",
        )

    def test_expired_order_is_displayed_as_expired(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="expired",
            paid=False,
        )

        response = self.client.get(
            reverse("orders:order_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"#{order.id}",
        )

        self.assertContains(
            response,
            "Expirée",
        )

    def test_cancelled_order_is_displayed_as_cancelled(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="cancelled",
            paid=False,
        )

        response = self.client.get(
            reverse("orders:order_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"#{order.id}",
        )

        self.assertContains(
            response,
            "Annulée",
        )
    
    def test_pending_order_detail_is_displayed_as_waiting_for_payment(self):
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
        )

        response = self.client.get(
            reverse(
                "orders:order_detail",
                args=[order.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"#{order.id}",
        )

        self.assertContains(
            response,
            "En attente de paiement",
        )

    def test_paid_order_detail_is_displayed_as_paid(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="paid",
            paid=True,
        )

        response = self.client.get(
            reverse(
                "orders:order_detail",
                args=[order.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"Commande #{order.id}",
        )

        self.assertContains(
            response,
            "Payée",
        )

        self.assertNotContains(
            response,
            "Payer maintenant",
        )

    def test_expired_order_detail_is_displayed_as_expired(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="expired",
            paid=False,
        )

        response = self.client.get(
            reverse(
                "orders:order_detail",
                args=[order.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"Commande #{order.id}",
        )

        self.assertContains(
            response,
            "Expirée",
        )

        self.assertNotContains(
            response,
            "Payer maintenant",
        )
        
    def test_cancelled_order_detail_is_displayed_as_cancelled(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="cancelled",
            paid=False,
        )

        response = self.client.get(
            reverse(
                "orders:order_detail",
                args=[order.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            f"Commande #{order.id}",
        )

        self.assertContains(
            response,
            "Annulée",
        )

        self.assertNotContains(
            response,
            "Payer maintenant",
        )

    def test_pending_order_detail_displays_cancel_button(self):
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
                + timedelta(minutes=30)
            ),
        )

        response = self.client.get(
            reverse(
                "orders:order_detail",
                args=[order.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Annuler la commande",
        )

    def test_paid_order_detail_does_not_display_cancel_button(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="Test",
            email="client@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            status="paid",
            paid=True,
        )

        response = self.client.get(
            reverse(
                "orders:order_detail",
                args=[order.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotContains(
            response,
            "Annuler la commande",
        )

    def test_expired_and_cancelled_orders_do_not_display_cancel_button(self):
        for status in ("expired", "cancelled"):
            with self.subTest(status=status):
                order = Order.objects.create(
                    user=self.user,
                    first_name="Client",
                    last_name="Test",
                    email="client@example.com",
                    phone="0102030405",
                    address="1 rue du Test",
                    postal_code="75000",
                    city="Paris",
                    status=status,
                    paid=False,
                )

                response = self.client.get(
                    reverse(
                        "orders:order_detail",
                        args=[order.id],
                    )
                )

                self.assertEqual(
                    response.status_code,
                    200,
                )

                self.assertNotContains(
                    response,
                    "Annuler la commande",
                )

        