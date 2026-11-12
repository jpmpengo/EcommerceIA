from django.test import TestCase

from orders.models import Order, OrderProcessingEvent


class OrderProcessingEventTests(TestCase):
    def test_event_is_recorded_for_order(self):
        order = Order.objects.create(
            first_name="John",
            last_name="Elese",
            email="john@example.com",
            phone="0102030405",
            address="9 rue du Test",
            postal_code="77700",
            city="Serris",
            country="FR",
            paid=True,
            status="paid",
        )

        event = OrderProcessingEvent.objects.create(
            order=order,
            event_type="customer_payment_received",
            source="automatic",
        )

        self.assertEqual(event.order, order)
        self.assertEqual(event.event_type, "customer_payment_received")
        self.assertEqual(event.source, "automatic")
        self.assertIsNotNone(event.created_at)
