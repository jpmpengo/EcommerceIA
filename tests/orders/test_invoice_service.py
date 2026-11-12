from django.test import TestCase

from orders.models import Order, OrderProcessingEvent
from orders.services.invoice_service import InvoiceService


class InvoiceServiceTests(TestCase):
    def test_create_for_paid_order_refuses_unpaid_order(self):
        order = Order.objects.create(
            first_name="John",
            last_name="Elese",
            email="jpmpengo@yahoo.fr",
            address="1 rue de Test",
            postal_code="75001",
            city="Paris",
            country="FR",
            paid=False,
            status="pending",
        )

        with self.assertRaises(ValueError):
            InvoiceService.create_for_paid_order(order)


    def test_create_for_paid_order_creates_invoice(self):
        from orders.models import Invoice, MerchantLegalEntity

        merchant = MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_active=True,
        )

        order = Order.objects.create(
            first_name="John",
            last_name="Elese",
            email="john@example.com",
            phone="0610101010",
            address="1 rue de Test",
            postal_code="75001",
            city="Paris",
            country="FR",
            billing_same_as_shipping=True,
            billing_first_name="John",
            billing_last_name="Elese",
            billing_address="1 rue de Test",
            billing_postal_code="75001",
            billing_city="Paris",
            billing_country="FR",
            paid=True,
            status="paid",
        )

        invoice = InvoiceService.create_for_paid_order(order)

        self.assertEqual(invoice.order, order)
        self.assertEqual(invoice.merchant, merchant)
        self.assertTrue(Invoice.objects.filter(order=order).exists())


class InvoiceServiceEventTests(TestCase):
    def test_invoice_creation_records_single_processing_event(self):
        from orders.models import MerchantLegalEntity

        MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_active=True,
        )

        order = Order.objects.create(
            first_name="John",
            last_name="Elese",
            email="john@example.com",
            phone="0610101010",
            address="1 rue de Test",
            postal_code="75001",
            city="Paris",
            country="FR",
            billing_same_as_shipping=True,
            billing_first_name="John",
            billing_last_name="Elese",
            billing_address="1 rue de Test",
            billing_postal_code="75001",
            billing_city="Paris",
            billing_country="FR",
            paid=True,
            status="paid",
        )

        InvoiceService.create_for_paid_order(order)
        InvoiceService.create_for_paid_order(order)

        events = OrderProcessingEvent.objects.filter(
            order=order,
            event_type="invoice_created",
        )
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.get().source, "automatic")
