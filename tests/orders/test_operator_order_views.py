from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from orders.models import Order, OrderItem, OrderProcessingEvent, SupplierOrder
from product_intelligence.models import ProductOpportunity, Supplier, SupplierOffer


User = get_user_model()


class OperatorOrderViewTests(TestCase):
    def setUp(self):
        group = Group.objects.create(name="Emma Operators")
        self.operator = User.objects.create_user(
            username="emma_operator",
            password="test-password",
        )
        self.operator.groups.add(group)
        self.customer = User.objects.create_user(
            username="customer",
            password="test-password",
        )
        self.order = Order.objects.create(
            user=self.customer,
            first_name="John",
            last_name="Elese",
            email="john@example.com",
            phone="0102030405",
            address="9 rue du Test",
            postal_code="77700",
            city="Serris",
            status="paid",
            paid=True,
        )

    def test_operator_can_list_all_customer_orders(self):
        self.client.force_login(self.operator)

        response = self.client.get(
            reverse("orders:operator_order_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Commandes clients")
        self.assertContains(response, f"Commande #{self.order.id}")
        self.assertContains(
            response,
            reverse(
                "orders:operator_order_detail",
                args=[self.order.id],
            ),
        )

    def test_operator_dashboard_indicators_and_filters(self):
        self.client.force_login(self.operator)
        url = reverse("orders:operator_order_list")
        response = self.client.get(url)
        self.assertEqual(response.context["dashboard_stats"]["total"], 1)
        self.assertEqual(response.context["dashboard_stats"]["paid"], 1)
        self.assertEqual(response.context["dashboard_stats"]["delivered"], 0)
        paid_response = self.client.get(url, {"status": "paid"})
        self.assertContains(paid_response, "Commande #" + str(self.order.id))
        delivered_response = self.client.get(url, {"status": "delivered"})
        self.assertEqual(delivered_response.context["orders"].count(), 0)
        self.assertContains(delivered_response, "Aucune commande pour ce filtre")

    def test_operator_can_view_delivery_details(self):
        self.client.force_login(self.operator)

        response = self.client.get(
            reverse(
                "orders:operator_order_detail",
                args=[self.order.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adresse de livraison")
        self.assertContains(response, "John Elese")
        self.assertContains(response, "9 rue du Test")
        self.assertContains(response, "77700 Serris")
        self.assertNotContains(response, "Continuer mes achats")

    def test_operator_sees_sandbox_supplier_order_without_misleading_label(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )
        SupplierOrder.objects.create(
            order=self.order,
            supplier=supplier,
            mode="sandbox",
            status="submitted",
            idempotency_key="TEST-SANDBOX-1",
            supplier_order_id="SD-TEST-1",
            supplier_status="DELIVERED",
            tracking_number="SBX-TEST-1",
            tracking_provider="CJPacket Ordinary I",
        )
        self.client.force_login(self.operator)

        response = self.client.get(
            reverse("orders:operator_order_detail", args=[self.order.id])
        )

        self.assertContains(response, "Commande fournisseur — CJdropshipping")
        self.assertContains(response, "SD-TEST-1")
        self.assertContains(response, "DELIVERED")
        self.assertContains(response, "SBX-TEST-1 — fictif")
        self.assertContains(response, "aucun débit")
        self.assertNotContains(response, "Simulation — aucun achat transmis")

    def test_customer_sees_fictitious_sandbox_tracking_without_clickable_url(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )
        SupplierOrder.objects.create(
            order=self.order,
            supplier=supplier,
            mode="sandbox",
            status="submitted",
            idempotency_key="TEST-SANDBOX-CUSTOMER",
            supplier_order_id="SD-TEST-CUSTOMER",
            supplier_status="DELIVERED",
            tracking_number="SBX-CUSTOMER-1",
            tracking_provider="CJPacket Ordinary I",
            tracking_url="https://t.17track.net/en#nums=SBX-CUSTOMER-1",
        )
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("orders:order_detail", args=[self.order.id])
        )

        self.assertContains(response, "SBX-CUSTOMER-1 — fictif")
        self.assertContains(response, "Simulation — aucun suivi réel")
        self.assertNotContains(response, "Suivre le colis")
        self.assertNotContains(response, 'href="https://t.17track.net')

    def test_customer_keeps_clickable_tracking_for_production_order(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )
        SupplierOrder.objects.create(
            order=self.order,
            supplier=supplier,
            mode="production",
            status="submitted",
            idempotency_key="TEST-PRODUCTION-CUSTOMER",
            supplier_order_id="CJ-REAL-1",
            supplier_status="SHIPPED",
            tracking_number="REAL-TRACK-1",
            tracking_provider="CJPacket Ordinary I",
            tracking_url="https://t.17track.net/en#nums=REAL-TRACK-1",
        )
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("orders:order_detail", args=[self.order.id])
        )

        self.assertContains(response, "REAL-TRACK-1")
        self.assertContains(response, "Suivre le colis")
        self.assertContains(response, 'href="https://t.17track.net')
        self.assertNotContains(response, "Simulation — aucun suivi réel")

    def test_operator_sees_processing_timeline(self):
        OrderProcessingEvent.objects.create(
            order=self.order,
            event_type="customer_payment_received",
            source="automatic",
        )
        OrderProcessingEvent.objects.create(
            order=self.order,
            event_type="supplier_order_submitted",
            source="manual",
        )

        self.client.force_login(self.operator)
        response = self.client.get(
            reverse("orders:operator_order_detail", args=[self.order.id])
        )

        self.assertContains(response, "Suivi du traitement")
        self.assertContains(response, "Paiement client reçu")
        self.assertContains(response, "Commande fournisseur transmise")

    def test_customer_does_not_see_processing_timeline(self):
        OrderProcessingEvent.objects.create(
            order=self.order,
            event_type="customer_payment_received",
            source="automatic",
        )

        self.client.force_login(self.customer)
        response = self.client.get(
            reverse("orders:order_detail", args=[self.order.id])
        )

        self.assertNotContains(response, "Suivi du traitement")
        self.assertNotContains(response, "Paiement client reçu")

    def test_operator_sees_prepare_supplier_order_action_when_ready(self):
        from products.models import Product

        self.order.country = "FR"
        self.order.save(update_fields=["country"])

        supplier = Supplier.objects.create(
            name="CJdropshipping-ready",
            country="CN",
            supplier_type="dropshipper",
        )
        product = Product.objects.create(
            name="Produit prêt fournisseur",
            description="Test",
            price="19.99",
            stock=5,
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name=product.name,
            supplier_product_id="VID-READY",
            purchase_price="5.00",
            shipping_cost="3.00",
            shipping_country="FR",
            currency="USD",
            supplier_verified_at=timezone.now(),
        )
        ProductOpportunity.objects.create(
            name=product.name,
            source_name=supplier.name,
            supplier_price=Decimal("5.00"),
            market_price=Decimal("19.99"),
            supplier_offer=offer,
            published_product=product,
            status="published",
        )
        OrderItem.objects.create(
            order=self.order,
            product=product,
            price="19.99",
            quantity=1,
        )

        self.client.force_login(self.operator)
        response = self.client.get(
            reverse("orders:operator_order_detail", args=[self.order.id])
        )

        self.assertContains(response, "Actions de traitement")
        self.assertContains(response, "Préparer en simulation")
        self.assertContains(
            response,
            reverse("orders:operator_prepare_supplier_order", args=[self.order.id]),
        )

    def test_operator_sees_submit_supplier_order_action_when_prepared(self):
        from orders.models import SupplierPreparation
        from products.models import Product

        self.order.country = "FR"
        self.order.save(update_fields=["country"])

        supplier = Supplier.objects.create(
            name="CJdropshipping-submit-ready",
            country="CN",
            supplier_type="dropshipper",
        )
        product = Product.objects.create(
            name="Produit prêt à transmettre",
            description="Test",
            price=Decimal("19.99"),
            stock=5,
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name=product.name,
            supplier_product_id="VID-SUBMIT",
            purchase_price=Decimal("5.00"),
            shipping_cost=Decimal("3.00"),
            shipping_country="FR",
            currency="USD",
            supplier_verified_at=timezone.now(),
        )
        ProductOpportunity.objects.create(
            name=product.name,
            source_name=supplier.name,
            supplier_price=Decimal("5.00"),
            market_price=Decimal("19.99"),
            supplier_offer=offer,
            published_product=product,
            status="published",
        )
        item = OrderItem.objects.create(
            order=self.order,
            product=product,
            price=Decimal("19.99"),
            quantity=1,
        )
        SupplierPreparation.objects.create(
            order_item=item,
            supplier_offer=offer,
            mode="simulation",
            destination_country="FR",
            quantity=1,
            source_currency="USD",
            target_currency="EUR",
            exchange_rate=Decimal("0.85"),
            purchase_original=Decimal("5.00"),
            shipping_original=Decimal("3.00"),
            purchase_converted=Decimal("4.25"),
            shipping_converted=Decimal("2.55"),
            base_cost=Decimal("6.80"),
            import_duty_rate=Decimal("0"),
            import_duty=Decimal("0"),
            landed_cost=Decimal("6.80"),
            rate_source="test",
            supplier_verified_at=timezone.now(),
            calculated_at=timezone.now(),
        )

        self.client.force_login(self.operator)
        response = self.client.get(
            reverse("orders:operator_order_detail", args=[self.order.id])
        )

        self.assertContains(response, "Transmettre au sandbox CJ")
        self.assertContains(
            response,
            reverse("orders:operator_submit_supplier_order", args=[self.order.id]),
        )

    @patch("orders.views.SupplierOrderSubmissionRunner")
    def test_operator_can_submit_supplier_order_manually_in_sandbox(self, runner):
        self.client.force_login(self.operator)
        runner.run.return_value = []

        response = self.client.post(
            reverse("orders:operator_submit_supplier_order", args=[self.order.id])
        )

        self.assertRedirects(
            response,
            reverse("orders:operator_order_detail", args=[self.order.id]),
        )
        runner.run.assert_called_once_with(
            self.order,
            sandbox=True,
            retry_failed=False,
            source="manual",
        )

    @patch("orders.views.SupplierPreparationRunner")
    def test_operator_can_prepare_supplier_order_manually(self, runner):
        self.client.force_login(self.operator)
        runner.run.return_value = []

        response = self.client.post(
            reverse("orders:operator_prepare_supplier_order", args=[self.order.id])
        )

        self.assertRedirects(
            response,
            reverse("orders:operator_order_detail", args=[self.order.id]),
        )
        runner.run.assert_called_once_with(
            self.order,
            source="manual",
        )

    @patch("orders.views.SupplierPreparationRunner")
    def test_customer_cannot_prepare_supplier_order(self, runner):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("orders:operator_prepare_supplier_order", args=[self.order.id])
        )

        self.assertRedirects(
            response,
            reverse("products:product_list"),
        )
        runner.run.assert_not_called()

    @patch("orders.views.SupplierOrderSubmissionRunner")
    def test_customer_cannot_submit_supplier_order(self, runner):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("orders:operator_submit_supplier_order", args=[self.order.id])
        )

        self.assertRedirects(
            response,
            reverse("products:product_list"),
        )
        runner.run.assert_not_called()

    def test_customer_cannot_access_operator_orders(self):
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("orders:operator_order_list")
        )

        self.assertRedirects(
            response,
            reverse("products:product_list"),
        )
