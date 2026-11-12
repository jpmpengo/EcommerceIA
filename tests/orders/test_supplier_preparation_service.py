from decimal import Decimal
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from orders.models import Order, OrderItem, OrderProcessingEvent, SupplierPreparation
from orders.services.customs_duty_service import CustomsDutyService
from orders.services.supplier_preparation_service import SupplierPreparationService
from product_intelligence.models import ProductOpportunity, Supplier, SupplierOffer
from product_intelligence.services.opportunity_cost_calculation import OpportunityCostCalculationService
from products.models import Product


User = get_user_model()


class SupplierPreparationServiceTests(TestCase):
    def setUp(self):
        customer = User.objects.create_user(username="customer")
        self.product = Product.objects.create(
            name="Produit test",
            description="Test",
            price=Decimal("14.99"),
            stock=9,
        )
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )
        self.offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Produit CJ Black 2XL",
            supplier_product_id="VID-1",
            supplier_parent_product_id="PID-1",
            supplier_sku="SKU-1",
            purchase_price=Decimal("1.14"),
            shipping_cost=Decimal("5.19"),
            shipping_country="FR",
            currency="USD",
            supplier_verified_at=timezone.now(),
        )
        ProductOpportunity.objects.create(
            name="Produit test",
            source_name="CJdropshipping",
            supplier_price=Decimal("0.98"),
            market_price=Decimal("14.99"),
            supplier_offer=self.offer,
            published_product=self.product,
            status="published",
        )
        order = Order.objects.create(
            user=customer,
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
        self.item = OrderItem.objects.create(
            order=order,
            product=self.product,
            price=Decimal("14.99"),
            quantity=1,
        )
        self.base_cost_service = Mock()
        self.base_cost_service.calculate.return_value = {
            "source_currency": "USD",
            "target_currency": "EUR",
            "exchange_rate": Decimal("0.857811"),
            "purchase_original": Decimal("1.14"),
            "shipping_original": Decimal("5.19"),
            "purchase_converted": Decimal("0.98"),
            "shipping_converted": Decimal("4.45"),
            "base_cost": Decimal("5.43"),
            "rate_source": "https://open.er-api.com/v6/latest",
        }

    def test_creates_frozen_simulation_with_customs_reserve(self):
        preparation = self._service().prepare(self.item)

        self.assertEqual(preparation.mode, "simulation")
        self.assertEqual(preparation.destination_country, "FR")
        self.assertEqual(preparation.base_cost, Decimal("5.43"))
        self.assertEqual(preparation.import_duty, Decimal("3.00"))
        self.assertEqual(preparation.import_duty_method, "eu_temporary_flat_fee")
        self.assertEqual(preparation.import_duty_unit_amount, Decimal("3.00"))
        self.assertEqual(preparation.landed_cost, Decimal("8.43"))
        self.assertEqual(preparation.sale_ttc, Decimal("14.99"))
        self.assertEqual(preparation.net_revenue, Decimal("12.49"))
        self.assertEqual(preparation.total_costs, Decimal("9.92"))
        self.assertEqual(preparation.projected_profit, Decimal("2.57"))
        self.assertIsNone(preparation.customs_clearance_fee)
        self.assertEqual(preparation.ioss_status, "unverified")
        self.assertEqual(SupplierPreparation.objects.count(), 1)

    def test_preparation_records_manual_processing_event(self):
        preparation = self._service().prepare(self.item, source="manual")

        event = OrderProcessingEvent.objects.get(
            order=self.item.order,
            event_type="supplier_preparation_created",
        )
        self.assertEqual(event.source, "manual")
        self.assertEqual(preparation.order_item, self.item)

    def test_repeated_preparation_does_not_duplicate_processing_event(self):
        service = self._service()
        service.prepare(self.item, source="manual")
        service.prepare(self.item, source="manual")

        self.assertEqual(
            OrderProcessingEvent.objects.filter(
                order=self.item.order,
                event_type="supplier_preparation_created",
            ).count(),
            1,
        )

    def test_rejects_country_mismatch(self):
        self.item.order.country = "BE"
        self.item.order.save(update_fields=["country"])

        with self.assertRaisesMessage(ValueError, "pays du transport"):
            self._service().prepare(self.item)

    def _service(self):
        return SupplierPreparationService(
            self.base_cost_service,
            OpportunityCostCalculationService(
                vat_rate=Decimal("0.20"),
                import_duty_rate=Decimal("0"),
                payment_rate=Decimal("0.015"),
                payment_fixed_fee=Decimal("0.25"),
                return_reserve_rate=Decimal("0.05"),
                safety_reserve_rate=Decimal("0.05"),
            ),
            CustomsDutyService(),
        )
