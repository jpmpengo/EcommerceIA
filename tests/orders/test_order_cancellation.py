from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from orders.models import OrderItem
from orders.services.reservation_service import (
    OrderReservationService,
)
from products.models import Product



User = get_user_model()


class OrderCancellationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_test",
            password="test12345",
        )

        self.client.login(
            username="client_test",
            password="test12345",
        )

    def test_client_can_cancel_own_pending_order(self):
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
        )

        response = self.client.post(
            reverse(
                "orders:order_cancel",
                args=[order.id],
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "cancelled",
        )

        self.assertFalse(
            order.paid
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_detail",
                args=[order.id],
            ),
        )

    def test_paid_order_cannot_be_cancelled(self):
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

        response = self.client.post(
            reverse(
                "orders:order_cancel",
                args=[order.id],
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "paid",
        )

        self.assertTrue(
            order.paid
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_detail",
                args=[order.id],
            ),
        )

    def test_client_cannot_cancel_another_users_order(self):
        other_user = User.objects.create_user(
            username="other_client",
            password="test12345",
        )

        order = Order.objects.create(
            user=other_user,
            first_name="Autre",
            last_name="Client",
            email="other@example.com",
            phone="0102030405",
            address="2 rue du Test",
            postal_code="75000",
            city="Paris",
            status="pending",
            paid=False,
        )

        response = self.client.post(
            reverse(
                "orders:order_cancel",
                args=[order.id],
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            order.status,
            "pending",
        )

        self.assertFalse(
            order.paid
        )

    def test_cancelling_pending_order_releases_reserved_stock(self):
        product = Product.objects.create(
            name="Support ordinateur portable",
            description="Produit de test.",
            price=Decimal("30.00"),
            stock=1,
            is_available=True,
        )

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

        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=1,
        )

        # Avant annulation :
        # le dernier exemplaire est réservé.
        self.assertEqual(
            OrderReservationService.get_available_stock(
                product
            ),
            0,
        )

        response = self.client.post(
            reverse(
                "orders:order_cancel",
                args=[order.id],
            )
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "cancelled",
        )

        # Après annulation :
        # la réservation ne compte plus.
        self.assertEqual(
            OrderReservationService.get_available_stock(
                product
            ),
            1,
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:order_detail",
                args=[order.id],
            ),
        )

