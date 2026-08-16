from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)
from product_intelligence.services.ebay_cj_bridge import (
    EbayCJBridgeService,
)


class FakeCJPipelineService:

    def build_opportunity_from_observation(
        self,
        supplier,
        product_id,
        market_observation,
    ):
        self.supplier = supplier
        self.product_id = product_id
        self.market_observation = market_observation

        return {
            "supplier": supplier.name,
            "product_id": product_id,
            "market_price": market_observation.observed_price,
        }


class EbayCJBridgeServiceTests(TestCase):

    def test_creates_opportunity_from_ebay_observation(self):
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

        pipeline = FakeCJPipelineService()

        service = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
        )

        result = service.create_opportunity(
            market_observation=observation,
            supplier=supplier,
            cj_product_id="CJ-123",
        )

        self.assertEqual(
            result["supplier"],
            "CJdropshipping",
        )

        self.assertEqual(
            result["product_id"],
            "CJ-123",
        )

        self.assertEqual(
            result["market_price"],
            Decimal("19.90"),
        )

        self.assertEqual(
            pipeline.market_observation,
            observation,
        )

    def test_searches_cj_product_from_observation_name(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-456",
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

        class FakeCJClient:

            def search_products(self, keyword):
                self.keyword = keyword

                return [
                    {
                        "id": "CJ-AUTO-123",
                        "nameEn": "Wireless Charger",
                        "sellPrice": "5.10",
                    }
                ]

        cj_client = FakeCJClient()
        pipeline = FakeCJPipelineService()

        service = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        result = service.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            cj_client.keyword,
            "Wireless Charger",
        )

        self.assertEqual(
            pipeline.product_id,
            "CJ-AUTO-123",
        )

        self.assertEqual(
            pipeline.market_observation,
            observation,
        )

        self.assertEqual(
            result["product_id"],
            "CJ-AUTO-123",
        )

    def test_selects_best_matching_cj_product(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-789",
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

        class FakeCJClient:

            def search_products(self, keyword):
                return [
                    {
                        "id": "CJ-WRONG-001",
                        "nameEn": "USB Cable",
                    },
                    {
                        "id": "CJ-BEST-002",
                        "nameEn": "Wireless Charger",
                    },
                    {
                        "id": "CJ-OTHER-003",
                        "nameEn": "Phone Stand",
                    },
                ]

        pipeline = FakeCJPipelineService()

        service = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=FakeCJClient(),
        )

        result = service.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            pipeline.product_id,
            "CJ-BEST-002",
        )

        self.assertEqual(
            result["product_id"],
            "CJ-BEST-002",
        )

    def test_rejects_cj_products_when_no_reliable_match_exists(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-NO-MATCH-001",
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

        class FakeCJClient:

            def search_products(self, keyword):
                return [
                    {
                        "id": "CJ-WRONG-001",
                        "nameEn": "USB Cable",
                    },
                    {
                        "id": "CJ-WRONG-002",
                        "nameEn": "Phone Case",
                    },
                    {
                        "id": "CJ-WRONG-003",
                        "nameEn": "Bluetooth Speaker",
                    },
                ]

        pipeline = FakeCJPipelineService()

        service = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=FakeCJClient(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "No reliable CJ product match found.",
        ):
            service.search_and_create_opportunity(
                market_observation=observation,
                supplier=supplier,
            )
        
    def test_accepts_similar_cj_product_name(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-SIMILAR-001",
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

        class FakeCJClient:

            def search_products(self, keyword):
                return [
                    {
                        "id": "CJ-SIMILAR-001",
                        "nameEn": "15W Wireless Charger",
                    },
                    {
                        "id": "CJ-WRONG-002",
                        "nameEn": "USB Cable",
                    },
                ]

        pipeline = FakeCJPipelineService()

        service = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=FakeCJClient(),
        )

        result = service.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            pipeline.product_id,
            "CJ-SIMILAR-001",
        )

        self.assertEqual(
            result["product_id"],
            "CJ-SIMILAR-001",
        )

    def test_selects_best_product_among_similar_candidates(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-BEST-MATCH-001",
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

        class FakeCJClient:

            def search_products(self, keyword):
                return [
                    {
                        "id": "CJ-GOOD-001",
                        "nameEn": "Wireless Charger Fast",
                    },
                    {
                        "id": "CJ-BEST-002",
                        "nameEn": "15W Wireless Fast Charger",
                    },
                    {
                        "id": "CJ-OTHER-003",
                        "nameEn": "Wireless Charging Stand",
                    },
                ]

        pipeline = FakeCJPipelineService()

        service = EbayCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=FakeCJClient(),
        )

        result = service.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            pipeline.product_id,
            "CJ-BEST-002",
        )

        self.assertEqual(
            result["product_id"],
            "CJ-BEST-002",
        )