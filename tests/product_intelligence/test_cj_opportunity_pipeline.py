from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import Supplier
from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)


class CJOpportunityPipelineTests(TestCase):

    def test_cj_offer_can_create_product_opportunity(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "image_url": "https://example.com/image.jpg",
            "purchase_price": "8.75",
            "product_url": "https://example.com/cj-product",
            "stock": 42,
            "shipping_cost": "3.20",
        }

        offer_service = CJSupplierOfferService()

        offer = offer_service.create_offer(
            supplier=supplier,
            product=product,
        )

        opportunity_service = SupplierOfferOpportunityService()

        opportunity = opportunity_service.create_opportunity(
            offer=offer,
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("8.75"),
        )

        self.assertEqual(
            opportunity.shipping_cost,
            Decimal("3.20"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.name,
            "Wireless Charger",
        )

    def test_cj_opportunity_has_expected_margin_and_score(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "image_url": "https://example.com/image.jpg",
            "purchase_price": "8.75",
            "product_url": "https://example.com/cj-product",
            "stock": 42,
            "shipping_cost": "3.20",
        }

        offer = CJSupplierOfferService().create_offer(
            supplier=supplier,
            product=product,
        )

        service = SupplierOfferOpportunityService()

        opportunity = service.create_opportunity(
            offer=offer,
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.get_total_cost(),
            Decimal("11.95"),
        )

        self.assertEqual(
            opportunity.get_estimated_margin(),
            Decimal("7.95"),
        )

        self.assertEqual(
            opportunity.opportunity_score,
            60,
        )