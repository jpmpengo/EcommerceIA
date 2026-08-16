from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from cart.cart import Cart
from orders.models import Order, OrderItem
from products.models import Product



User = get_user_model()


class CartReservationAvailabilityTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_a",
            password="test12345",
        )

        self.product = Product.objects.create(
            name="Support ordinateur portable",
            description=(
                "Support pratique pour ordinateur portable "
                "adapté au travail quotidien."
            ),
            price=Decimal("30.00"),
            stock=1,
            is_available=True,
        )

    def test_cart_detects_product_fully_reserved(self):
        # Le dernier exemplaire est réservé
        # par une commande encore active.
        order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="A",
            email="a@example.com",
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
            quantity=1,
        )

        # Panier d'un deuxième client.
        session = self.client.session

        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            }
        }

        session.save()

        request = SimpleNamespace(
            session=session
        )

        cart = Cart(request)

        self.assertFalse(
            cart.has_sufficient_stock()
        )

        # Le stock physique reste bien à 1.
        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            1,
        )

    def test_cart_view_disables_checkout_when_stock_is_reserved(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="A",
            email="a@example.com",
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
            quantity=1,
        )

        # Panier du deuxième client.
        session = self.client.session

        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            }
        }

        session.save()

        response = self.client.get(
            reverse("cart:cart_detail")
        )  

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "can_checkout",
            response.context,
        )

        self.assertFalse(
            response.context["can_checkout"]
        )

    def test_cart_template_hides_checkout_when_stock_is_reserved(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="A",
            email="a@example.com",
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
            quantity=1,
        )

        session = self.client.session

        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            }
        }

        session.save()

        response = self.client.get(
            reverse("cart:cart_detail")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Ce produit est temporairement réservé par un autre client.",
        )

        self.assertContains(
            response,
            "Continuer mes achats",
        )

        self.assertNotContains(
            response,
            "Valider la commande",
        )

    def test_checkout_becomes_available_after_reservation_expires(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="A",
            email="a@example.com",
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
            quantity=1,
        )

        session = self.client.session

        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            }
        }

        session.save()

        response = self.client.get(
            reverse("cart:cart_detail")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.context["can_checkout"]
        )

        self.assertContains(
            response,
            "Valider la commande",
        )

        self.assertNotContains(
            response,
            "Ce produit est temporairement réservé par un autre client.",
        )

        self.assertNotContains(
            response,
            "Continuer mes achats",
        )

   

