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
from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)
from product_intelligence.services.ebay_cj_bridge import (
    EbayCJBridgeService,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)


class FakeCJClient:

    def search_products(self, keyword):
        self.keyword = keyword

        return [
            {
                "id": "CJ-WRONG-001",
                "nameEn": "USB Cable",
            },
            {
                "id": "CJ-BEST-002",
                "nameEn": "15W Wireless Fast Charger",
            },
        ]

    def get_product_detail(self, product_id):
        self.product_id = product_id

        return {
            "pid": product_id,
            "productNameEn": "15W Wireless Fast Charger",
            "sellPrice": "7.30",
        }

    def normalize_product(self, product):
        return {
            "external_id": product["pid"],
            "name": product["productNameEn"],
            "purchase_price": product["sellPrice"],
            "currency": "USD",
        }

    def get_product_variants(self, product_id):
        return [
            {
                "vid": "VARIANT-123",
                "pid": product_id,
                "variantNameEn": "15W Wireless Fast Charger Black",
                "variantSellPrice": "7.30",
            }
        ]

    def get_variant_stock(self, variant_id):
        self.variant_id = variant_id
        return 500


class FakeExchangeRateClient:

    def get_rate(
        self,
        from_currency,
        to_currency,
    ):
        self.from_currency = from_currency
        self.to_currency = to_currency

        return Decimal("0.86")


class EbayCJIntegrationTests(TestCase):

    def test_ebay_observation_creates_cj_product_opportunity(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-INTEGRATION-001",
            name="Wireless Fast Charger 15W",
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

        cj_client = FakeCJClient()
        exchange_rate_client = FakeExchangeRateClient()

        cj_pipeline = CJPipelineService(
            client=cj_client,
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=CurrencyConversionService(),
            exchange_rate_client=exchange_rate_client,
        )

        bridge = EbayCJBridgeService(
            cj_pipeline_service=cj_pipeline,
            cj_client=cj_client,
        )

        opportunity = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        offer = supplier.offers.get()

        self.assertEqual(
            cj_client.keyword,
            "Wireless Fast Charger 15W",
        )

        self.assertEqual(
            cj_client.product_id,
            "CJ-BEST-002",
        )

        self.assertEqual(
            cj_client.variant_id,
            "VARIANT-123",
        )

        self.assertEqual(
            offer.market_observation,
            observation,
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("6.28"),
        )

        self.assertEqual(
            offer.currency,
            "EUR",
        )

        self.assertEqual(
            offer.stock,
            500,
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("6.28"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.name,
            "15W Wireless Fast Charger",
        )

        self.assertEqual(
            exchange_rate_client.from_currency,
            "USD",
        )

        self.assertEqual(
            exchange_rate_client.to_currency,
            "EUR",
        )

    def test_preserves_decimal_precision_for_cj_float_price(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-DECIMAL-001",
            name="Wireless controller charger",
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

        class FloatPriceCJClient:

            def search_products(self, keyword):
                return [
                    {
                        "id": "CJ-FLOAT-001",
                        "nameEn": "Wireless controller charger",
                    }
                ]

            def get_product_detail(self, product_id):
                return {
                    "pid": product_id,
                    "productNameEn": "Wireless controller charger",
                    "sellPrice": 5.1,
                }

            def normalize_product(self, product):
                return {
                    "external_id": product["pid"],
                    "name": product["productNameEn"],
                    "purchase_price": product["sellPrice"],
                    "currency": "USD",
                }

            def get_product_variants(self, product_id):
                return []

        class FixedExchangeRateClient:

            def get_rate(
                self,
                from_currency,
                to_currency,
            ):
                return Decimal("0.866478")

        cj_client = FloatPriceCJClient()

        pipeline = CJPipelineService(
            client=cj_client,
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=CurrencyConversionService(),
            exchange_rate_client=FixedExchangeRateClient(),
        )

        bridge = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        opportunity = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        offer = supplier.offers.get()

        self.assertEqual(
            offer.purchase_price,
            Decimal("4.42"),
        )

        self.assertEqual(
            offer.currency,
            "EUR",
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("4.42"),
        )

        self.assertEqual(
            opportunity.get_estimated_margin(),
            Decimal("15.48"),
        )


        