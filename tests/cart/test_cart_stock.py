from decimal import Decimal

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from products.models import Product


class CartStockTests(TestCase):

    def test_out_of_stock_product_cannot_be_added_to_cart(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Test",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        response = self.client.get(
            reverse(
                "cart:cart_add",
                args=[product.id],
            ),
            follow=True,
        )

        messages = [
            str(message)
            for message in get_messages(
                response.wsgi_request
            )
        ]

        self.assertIn(
            "Ce produit est en rupture de stock.",
            messages,
        )

        session = self.client.session

        self.assertEqual(
            session.get("cart", {}),
            {},
        )

    def test_out_of_stock_product_remains_visible_in_catalog(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Test",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        response = self.client.get(
            reverse("products:product_list")
        )

        self.assertContains(
            response,
            "Wireless Charger",
        )