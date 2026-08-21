from decimal import Decimal

from django.test import TestCase

from orders.models import Order
from products.models import Product

from unittest.mock import Mock, patch

from datetime import timedelta

from django.utils import timezone


class GuestCheckoutViewTests(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Casque Bluetooth ANC",
            description="Casque Bluetooth de test.",
            price=Decimal("79.90"),
            stock=5,
            is_available=True,
        )

        session = self.client.session

        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            },
        }

        session.save()

        self.checkout_data = {
            "first_name": "Elese",
            "last_name": "Client",
            "email": "elese@example.com",
            "phone": "0102030405",
            "address": "1 rue du Commerce",
            "postal_code": "75000",
            "city": "Paris",
        }

    def test_guest_checkout_redirects_to_stable_confirmation_page(
        self,
    ):
        response = self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        expected_url = (
            f"/commande/confirmation/{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            expected_url,
        )

        confirmation_response = self.client.get(
            expected_url
        )

        self.assertEqual(
            confirmation_response.status_code,
            200,
        )

        self.assertTemplateUsed(
            confirmation_response,
            "orders/order_created.html",
        )

        self.assertEqual(
            confirmation_response.context["order"],
            order,
        )

        refreshed_response = self.client.get(
            expected_url
        )

        self.assertEqual(
            refreshed_response.status_code,
            200,
        )

    def test_guest_can_view_order_created_in_same_session(
        self,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        response = self.client.get(
            f"/commande/mes-commandes/{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "orders/order_detail.html",
        )

        self.assertEqual(
            response.context["order"],
            order,
        )

    @patch(
        "orders.views.stripe.checkout.Session.create"
    )
    def test_guest_can_start_payment_for_own_order(
        self,
        stripe_create,
    ):
        checkout_session = Mock()

        checkout_session.id = (
            "cs_test_guest_order"
        )

        checkout_session.url = (
            "https://checkout.stripe.test/"
            "guest-order"
        )

        stripe_create.return_value = (
            checkout_session
        )

        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        response = self.client.get(
            f"/commande/paiement/{order.id}/"
        )

        self.assertEqual(
            response.status_code,
            303,
        )

        self.assertEqual(
            response["Location"],
            checkout_session.url,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.stripe_checkout_session_id,
            checkout_session.id,
        )

        stripe_create.assert_called_once()

    @patch(
        "orders.views.stripe.checkout.Session.retrieve"
    )
    def test_guest_can_view_payment_success_for_own_order(
        self,
        stripe_retrieve,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        order.stripe_checkout_session_id = (
            "cs_test_guest_success"
        )

        order.save(
            update_fields=[
                "stripe_checkout_session_id",
            ]
        )

        checkout_session = Mock()

        checkout_session.id = (
            "cs_test_guest_success"
        )

        checkout_session.payment_status = (
            "paid"
        )

        checkout_session.metadata.order_id = str(
            order.id
        )

        stripe_retrieve.return_value = (
            checkout_session
        )

        response = self.client.get(
            (
                "/commande/paiement/succes/"
                "?session_id=cs_test_guest_success"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "orders/payment_success.html",
        )

        self.assertEqual(
            response.context["order"],
            order,
        )

        order.refresh_from_db()
        self.product.refresh_from_db()

        self.assertTrue(
            order.paid
        )

        self.assertEqual(
            order.status,
            "paid",
        )

        self.assertEqual(
            self.product.stock,
            4,
        )

        stripe_retrieve.assert_called_once_with(
            "cs_test_guest_success"
        )

    def test_guest_can_list_orders_created_in_same_session(
        self,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        response = self.client.get(
            "/commande/mes-commandes/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "orders/order_list.html",
        )

        self.assertContains(
            response,
            f"#{order.id}",
        )

        self.assertIn(
            order,
            response.context["orders"],
        )

    def test_guest_can_cancel_own_pending_order(
        self,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        response = self.client.post(
            (
                "/commande/mes-commandes/"
                f"{order.id}/annuler/"
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "cancelled",
        )

        self.assertRedirects(
            response,
            (
                "/commande/mes-commandes/"
                f"{order.id}/"
            ),
        )

    def test_order_list_expires_accessible_overdue_orders(
        self,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        order.reservation_expires_at = (
            timezone.now()
            - timedelta(minutes=1)
        )

        order.save(
            update_fields=[
                "reservation_expires_at",
            ]
        )

        response = self.client.get(
            "/commande/mes-commandes/"
        )

        order.refresh_from_db()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            order.status,
            "expired",
        )

        self.assertContains(
            response,
            "Expirée",
        )

    def test_order_detail_expires_accessible_overdue_order(
        self,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        order.reservation_expires_at = (
            timezone.now()
            - timedelta(minutes=1)
        )

        order.save(
            update_fields=[
                "reservation_expires_at",
            ]
        )

        response = self.client.get(
            (
                "/commande/mes-commandes/"
                f"{order.id}/"
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            order.status,
            "expired",
        )

        self.assertContains(
            response,
            "Expirée",
        )

        self.assertNotContains(
            response,
            "Payer maintenant",
        )

    def test_confirmation_expires_accessible_overdue_order(
        self,
    ):
        self.client.post(
            "/commande/creer/",
            data=self.checkout_data,
        )

        order = Order.objects.get()

        order.reservation_expires_at = (
            timezone.now()
            - timedelta(minutes=1)
        )

        order.save(
            update_fields=[
                "reservation_expires_at",
            ]
        )

        response = self.client.get(
            (
                "/commande/confirmation/"
                f"{order.id}/"
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            order.status,
            "expired",
        )

        self.assertNotContains(
            response,
            "Payer maintenant",
        )
