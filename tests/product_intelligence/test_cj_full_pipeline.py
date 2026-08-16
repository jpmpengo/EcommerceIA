from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)
from product_intelligence.services.cj_pipeline import (
    CJPipelineService,
)
from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)


class FakeCJClient:

    def get_product_detail(self, product_id):
        return {
            "id": product_id,
            "nameEn": "Wireless Charger",
            "bigImage": "https://example.com/image.jpg",
            "sellPrice": "8.75",
        }

    def normalize_product(self, product):
        return {
            "external_id": product["id"],
            "name": product["nameEn"],
            "image_url": product["bigImage"],
            "purchase_price": product["sellPrice"],
        }

    def get_product_variants(self, product_id):
        return [
            {
                "vid": "VARIANT-123",
                "pid": product_id,
                "variantNameEn": "Black",
                "variantSellPrice": "9.25",
            }
        ]

    def get_variant_stock(self, variant_id):
        return 42


class CJFullPipelineTests(TestCase):

    def test_market_observation_can_create_cj_opportunity(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-123",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        pipeline = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
        )

        opportunity = pipeline.build_opportunity_from_observation(
            supplier=supplier,
            product_id="CJ-123",
            market_observation=observation,
        )

        offer = supplier.offers.get()

        self.assertEqual(
            offer.market_observation,
            observation,
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("9.25"),
        )

        self.assertEqual(
            offer.stock,
            42,
        )

        self.assertEqual(
            opportunity.name,
            "Wireless Charger",
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("9.25"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.get_total_cost(),
            Decimal("9.25"),
        )

        self.assertEqual(
            opportunity.get_estimated_margin(),
            Decimal("10.65"),
        )

        self.assertEqual(
            opportunity.opportunity_score,
            60,
        )

        