from django.test import TestCase

from orders.models import Invoice, MerchantLegalEntity, Order


class InvoiceTests(TestCase):

    def test_invoice_can_be_created_for_paid_order(self):
        merchant = MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            siren="123456789",
            siret="12345678900010",
            vat_number="FR00123456789",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            email="contact@ecommerceia.local",
            phone="0102030405",
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

        invoice = Invoice.objects.create(
            order=order,
            merchant=merchant,
            number="FAC-2026-0001",
        )

        self.assertEqual(invoice.order, order)
        self.assertEqual(invoice.merchant, merchant)
        self.assertEqual(invoice.number, "FAC-2026-0001")


    def test_confirm_payment_creates_invoice_automatically(self):
        merchant = MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            siren="123456789",
            siret="12345678900010",
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
            paid=False,
            status="pending",
        )

        from orders.services.payment_service import OrderPaymentService
        OrderPaymentService.confirm_payment(order.id, "cs_test_invoice")

        order.refresh_from_db()
        self.assertTrue(order.paid)
        self.assertTrue(hasattr(order, "invoice"))
        self.assertEqual(order.invoice.merchant, merchant)


    def test_confirm_payment_does_not_create_duplicate_invoice(self):
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
            paid=False,
            status="pending",
        )

        from orders.services.payment_service import OrderPaymentService
        OrderPaymentService.confirm_payment(order.id, "cs_test_invoice")
        OrderPaymentService.confirm_payment(order.id, "cs_test_invoice")

        self.assertEqual(Invoice.objects.filter(order=order).count(), 1)


    def test_invoice_keeps_merchant_and_billing_snapshots(self):
        merchant = MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            trade_name="EcommerceIA",
            siren="123456789",
            siret="12345678900010",
            vat_number="FR00123456789",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            email="contact@ecommerceia.local",
            phone="0102030405",
            is_active=True,
        )

        order = Order.objects.create(
            first_name="John",
            last_name="Elese",
            email="john@example.com",
            phone="0610101010",
            address="1 rue Livraison",
            postal_code="75001",
            city="Paris",
            country="FR",
            billing_same_as_shipping=False,
            billing_first_name="John",
            billing_last_name="Facturation",
            billing_address="20 avenue Facturation",
            billing_postal_code="69001",
            billing_city="Lyon",
            billing_country="FR",
            paid=False,
            status="pending",
        )

        from orders.services.payment_service import OrderPaymentService
        OrderPaymentService.confirm_payment(order.id, "cs_test_snapshot")

        invoice = Invoice.objects.get(order=order)

        self.assertEqual(invoice.merchant_legal_name, "EcommerceIA Demo SAS")
        self.assertEqual(invoice.merchant_siret, "12345678900010")
        self.assertEqual(invoice.billing_first_name, "John")
        self.assertEqual(invoice.billing_last_name, "Facturation")
        self.assertEqual(invoice.billing_address, "20 avenue Facturation")
        self.assertEqual(invoice.billing_postal_code, "69001")
        self.assertEqual(invoice.billing_city, "Lyon")
        self.assertEqual(invoice.billing_country, "FR")


    def test_invoice_stores_total_ht_vat_and_ttc_from_order_items(self):
        from decimal import Decimal
        from products.models import Product
        from orders.models import OrderItem
        from orders.services.payment_service import OrderPaymentService

        MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_active=True,
        )

        product = Product.objects.create(
            name="Produit test facture",
            price=Decimal("12.12"),
            stock=10,
            is_available=True,
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
            paid=False,
            status="pending",
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal("12.12"),
            quantity=1,
        )

        OrderPaymentService.confirm_payment(order.id, "cs_test_totals")
        invoice = Invoice.objects.get(order=order)

        self.assertEqual(invoice.total_ttc, Decimal("12.12"))
        self.assertEqual(invoice.vat_rate, Decimal("0.20"))
        self.assertEqual(invoice.total_ht, Decimal("10.10"))
        self.assertEqual(invoice.vat_amount, Decimal("2.02"))


    def test_invoice_creates_item_snapshot_from_order_item(self):
        from decimal import Decimal
        from products.models import Product
        from orders.models import InvoiceItem, OrderItem
        from orders.services.payment_service import OrderPaymentService

        MerchantLegalEntity.objects.create(
            legal_name="EcommerceIA Demo SAS",
            address="10 rue du Commerce",
            postal_code="75001",
            city="Paris",
            country="FR",
            is_active=True,
        )

        product = Product.objects.create(
            name="Gamelle anti-glouton en silicone pour chien",
            price=Decimal("12.12"),
            stock=10,
            is_available=True,
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
            paid=False,
            status="pending",
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal("12.12"),
            quantity=2,
        )

        OrderPaymentService.confirm_payment(order.id, "cs_test_invoice_item")
        invoice = Invoice.objects.get(order=order)
        item = InvoiceItem.objects.get(invoice=invoice)

        self.assertEqual(item.description, "Gamelle anti-glouton en silicone pour chien")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price_ttc, Decimal("12.12"))
        self.assertEqual(item.total_ttc, Decimal("24.24"))


    def test_invoice_item_keeps_product_reference_for_image(self):
        from decimal import Decimal
        from products.models import Product
        from orders.models import InvoiceItem, OrderItem
        from orders.services.payment_service import OrderPaymentService

        MerchantLegalEntity.objects.create(legal_name="EcommerceIA Demo SAS", address="10 rue du Commerce", postal_code="75001", city="Paris", country="FR", is_active=True)
        product = Product.objects.create(name="Produit avec image", price=Decimal("12.12"), stock=10, is_available=True)
        order = Order.objects.create(first_name="John", last_name="Elese", email="john@example.com", phone="0610101010", address="1 rue de Test", postal_code="75001", city="Paris", country="FR", billing_same_as_shipping=True, billing_first_name="John", billing_last_name="Elese", billing_address="1 rue de Test", billing_postal_code="75001", billing_city="Paris", billing_country="FR", paid=False, status="pending")
        OrderItem.objects.create(order=order, product=product, price=Decimal("12.12"), quantity=1)
        OrderPaymentService.confirm_payment(order.id, "cs_test_invoice_image")
        item = InvoiceItem.objects.get(invoice__order=order)
        self.assertEqual(item.product, product)
