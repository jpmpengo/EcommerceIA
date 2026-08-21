from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Product

from orders.models import Order, OrderItem
from orders.services.payment_service import (
    OrderPaymentService,
)

from datetime import timedelta
from django.utils import timezone




User = get_user_model()


class StockPaymentWorkflowTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="client_test",
            password="test12345",
        )

        self.product = Product.objects.create(
            name="Support ordinateur portable",
            description=(
                "Support pratique pour ordinateur portable "
                "destiné au travail quotidien."
            ),
            price=Decimal("30.00"),
            stock=5,
            is_available=True,
        )

        self.client.login(
            username="client_test",
            password="test12345",
        )

    def test_stock_is_not_decreased_before_payment(self):
        session = self.client.session

        session["cart"] = {
            str(self.product.id): {
                "quantity": 1,
                "price": str(self.product.price),
            }
        }

        session.save()

        response = self.client.post(
            reverse("orders:order_create"),
            {
                "first_name": "Jean",
                "last_name": "Test",
                "email": "jean@example.com",
                "phone": "0102030405",
                "address": "1 rue du Test",
                "postal_code": "75000",
                "city": "Paris",
            },
        )

        order = Order.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "orders:order_created",
                args=[
                    order.id,
                ],
            ),
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            5,
        )  

    def test_stock_is_decreased_after_payment(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=False,
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )

        # Avant paiement
        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            5,
        )

        self.assertFalse(
            order.paid
        )

        # Stripe confirme le paiement
        OrderPaymentService.confirm_payment(
            order_id=order.id,
            stripe_session_id="cs_test_123",
        )

        # Relecture depuis la base
        self.product.refresh_from_db()
        order.refresh_from_db()

        # Le stock doit être diminué
        self.assertEqual(
            self.product.stock,
            4,
        )

        # La commande doit être payée
        self.assertTrue(
            order.paid
        )

        # La session Stripe doit être enregistrée
        self.assertEqual(
            order.stripe_checkout_session_id,
            "cs_test_123",
        )
    
    def test_payment_confirmation_does_not_decrease_stock_twice(self):
        order = Order.objects.create(
            user=self.user,
            first_name="Jean",
            last_name="Test",
            email="jean@example.com",
            phone="0102030405",
            address="1 rue du Test",
            postal_code="75000",
            city="Paris",
            paid=False,
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )

        # Première confirmation Stripe
        OrderPaymentService.confirm_payment(
            order_id=order.id,
            stripe_session_id="cs_test_123",
        )

        self.product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            4,
        )

        self.assertTrue(
            order.paid
        )

        # Stripe renvoie la confirmation une deuxième fois
        OrderPaymentService.confirm_payment(
            order_id=order.id,
            stripe_session_id="cs_test_123",
        )

        self.product.refresh_from_db()
        order.refresh_from_db()

        # Le stock doit rester à 4
        self.assertEqual(
            self.product.stock,
            4,
        )

        self.assertTrue(
            order.paid
        )

    def test_second_payment_fails_when_stock_is_exhausted(self):
        self.product.stock = 1
        self.product.save(
        update_fields=["stock"]
        )

        order_a = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="A",
            email="a@example.com",
            phone="0102030405",
            address="1 rue A",
            postal_code="75000",
            city="Paris",
            paid=False,
        )

        OrderItem.objects.create(
            order=order_a,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )

        order_b = Order.objects.create(
            user=self.user,
            first_name="Client",
            last_name="B",
            email="b@example.com",
            phone="0102030406",
            address="2 rue B",
            postal_code="75000",
            city="Paris",
            paid=False,
        )

        OrderItem.objects.create(
            order=order_b,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )

        # Premier paiement : dernier exemplaire vendu
        OrderPaymentService.confirm_payment(
            order_id=order_a.id,
            stripe_session_id="cs_test_a",
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            0,
        )

        # Deuxième paiement : doit être refusé côté métier
        with self.assertRaises(ValueError):
            OrderPaymentService.confirm_payment(
                order_id=order_b.id,
                stripe_session_id="cs_test_b",
            )   

        self.product.refresh_from_db()
        order_b.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            0,
        )

        self.assertFalse(
            order_b.paid
        )

    def test_successful_payment_marks_order_as_paid(self):
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

        OrderPaymentService.confirm_payment(
            order_id=order.id,
            stripe_session_id="cs_test_123",
        )

        order.refresh_from_db()

        self.assertTrue(
            order.paid
        )

        self.assertEqual(
            order.status,
            "paid",
        )

        self.assertEqual(
            order.stripe_checkout_session_id,
            "cs_test_123",
        )

    def test_payment_of_last_item_makes_product_unavailable(self):
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
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=1,
        )

        OrderPaymentService.confirm_payment(
            order_id=order.id,
            stripe_session_id="cs_test_last_item",
        )

        product.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(
            product.stock,
            0,
        )

        self.assertFalse(
            product.is_available,
        )

        self.assertTrue(
            order.paid,
        )

        self.assertEqual(
            order.status,
            "paid",
        )
    
    def test_paid_out_of_stock_product_disappears_from_product_list(self):
        product = Product.objects.create(
            name="Produit dernier exemplaire",
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
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=1,
        )

        # Avant paiement, le produit est visible.
        response = self.client.get(
            reverse("products:product_list")
        )

        self.assertContains(
            response,
            "Produit dernier exemplaire",
        )

        # Paiement du dernier exemplaire.
        OrderPaymentService.confirm_payment(
            order_id=order.id,
            stripe_session_id="cs_test_catalog",
        )

        product.refresh_from_db()

        self.assertEqual(
            product.stock,
            0,
        )

        self.assertFalse(
            product.is_available,
        )

        # Après paiement, il disparaît du catalogue.
        response = self.client.get(
            reverse("products:product_list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotContains(
            response,
            "Produit dernier exemplaire",
        )
 


