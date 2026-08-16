from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from orders.models import Order, OrderItem
from orders.services.reservation_service import (
    OrderReservationService,
)
from products.models import Product


User = get_user_model()


class OrderReservationServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_test",
            password="test12345",
        )

        self.product = Product.objects.create(
            name="Casque Bluetooth",
            description=(
                "Casque Bluetooth confortable avec une description "
                "suffisamment détaillée pour les besoins du test."
            ),
            price=Decimal("79.90"),
            stock=5,
            is_available=True,
        )

    def test_pending_order_reduces_available_stock(self):
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
                + timedelta(minutes=30)
            ),
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=2,
        )

        available_stock = (
            OrderReservationService.get_available_stock(
                self.product
            )
        )

        # Stock physique inchangé.
        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            5,
        )

        # Deux articles sont réservés.
        self.assertEqual(
            available_stock,
            3,
        )

    def test_expired_reservation_does_not_reduce_available_stock(self):
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

        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=2,
        )

        available_stock = (
            OrderReservationService.get_available_stock(
                self.product
            )
        )

        self.product.refresh_from_db()

        # Le stock physique reste inchangé.
        self.assertEqual(
            self.product.stock,
            5,
        )

        # La réservation est expirée :
        # les 5 articles sont donc disponibles.
        self.assertEqual(
            available_stock,
            5,
        )

    def test_cannot_reserve_more_than_available_stock(self):
        first_order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="A",
            email="a@example.com",
            phone="0102030405",
            address="1 rue A",
            postal_code="75000",
            city="Paris",
            status="pending",
            paid=False,
            reservation_expires_at=(
                timezone.now()
                + timedelta(minutes=30)
            ),
        )   

        # La première commande réserve 4 articles sur 5.
        OrderItem.objects.create(
            order=first_order,
            product=self.product,
            price=self.product.price,
            quantity=4,
        )

        second_order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="B",
            email="b@example.com",
            phone="0102030406",
            address="2 rue B",
            postal_code="75000",
            city="Paris",
            status="pending",
            paid=False,
            reservation_expires_at=(
                timezone.now()
                + timedelta(minutes=30)
            ),
        )

        # Il ne reste qu'un article disponible.
        available_stock = (
            OrderReservationService.get_available_stock(
                self.product
            )
        )

        self.assertEqual(
            available_stock,
            1,
        )

        # La deuxième commande tente d'en réserver 2.
        with self.assertRaises(ValueError):
            OrderReservationService.reserve(
                order=second_order,
                product=self.product,
                quantity=2,
            )

        # Aucune ligne ne doit avoir été créée
        # pour la deuxième commande.
        self.assertFalse(
            second_order.items.filter(
                product=self.product
            ).exists()
        )

        # Le stock physique ne doit jamais être modifié.
        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            5,
        )   

    def test_paid_order_does_not_reduce_available_stock_as_reservation(self):
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
            reservation_expires_at=(
                timezone.now()
                + timedelta(minutes=30)
            ),
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=2,
        )

        available_stock = (
            OrderReservationService.get_available_stock(
                self.product
            )
        )

        self.assertEqual(
            available_stock,
            5,
        )

    def test_expired_pending_order_can_be_marked_expired(self):
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

        OrderReservationService.expire_order(
            order
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "expired",
        )

        self.assertFalse(
            order.paid
        )

    def test_active_pending_order_is_not_marked_expired(self):
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
                + timedelta(minutes=30)
            ),
        )

        OrderReservationService.expire_order(
            order
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            "pending",
        )

        self.assertFalse(
            order.paid
        )

    def test_expire_pending_orders_expires_only_outdated_orders(self):
        expired_order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="Expired",
            email="expired@example.com",
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

        active_order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="Active",
            email="active@example.com",
            phone="0102030406",
            address="2 rue du Test",
            postal_code="75000",
            city="Paris",
            status="pending",
            paid=False,
            reservation_expires_at=(
                timezone.now()
                + timedelta(minutes=30)
            ),
        )

        OrderReservationService.expire_pending_orders()

        expired_order.refresh_from_db()
        active_order.refresh_from_db()

        self.assertEqual(
            expired_order.status,
            "expired",
        )   

        self.assertEqual(
            active_order.status,
            "pending",
        )