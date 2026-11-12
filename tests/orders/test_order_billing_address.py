from django.test import TestCase

from orders.models import Order


class OrderBillingAddressTests(TestCase):

    def test_order_can_store_billing_address_separately(self):
        order = Order.objects.create(
            first_name="Elese",
            last_name="Client",
            email="elese@example.com",
            phone="0102030405",
            address="1 rue Livraison",
            postal_code="75001",
            city="Paris",
            country="FR",
            billing_same_as_shipping=False,
            billing_first_name="Elese",
            billing_last_name="Facturation",
            billing_address="20 avenue Facturation",
            billing_postal_code="69001",
            billing_city="Lyon",
            billing_country="FR",
        )

        self.assertFalse(order.billing_same_as_shipping)
        self.assertEqual(order.billing_first_name, "Elese")
        self.assertEqual(order.billing_last_name, "Facturation")
        self.assertEqual(order.billing_address, "20 avenue Facturation")
        self.assertEqual(order.billing_postal_code, "69001")
        self.assertEqual(order.billing_city, "Lyon")
        self.assertEqual(order.billing_country, "FR")

        self.assertEqual(order.address, "1 rue Livraison")
        self.assertEqual(order.city, "Paris")
