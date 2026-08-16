from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)
from product_intelligence.services.etsy_cj_bridge import (
    EtsyCJBridgeService,
)


class EtsyCJBridgeServiceTests(TestCase):

    def test_creates_opportunity_from_etsy_observation(self):
        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="123456789",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url=(
                "https://www.etsy.com/listing/123456789"
            ),
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        cj_client = Mock()

        cj_client.search_products.return_value = [
            {
                "id": "CJ-123",
                "name": "Wireless Charger",
            }
        ]

        pipeline = Mock()

        expected_opportunity = Mock()

        pipeline.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        bridge = EtsyCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        result = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        cj_client.search_products.assert_called_once_with(
            keyword="Wireless Charger",
        )

        pipeline.build_opportunity_from_observation.assert_called_once_with(
            supplier=supplier,
            product_id="CJ-123",
            market_observation=observation,
        )

        self.assertIs(
            result,
            expected_opportunity,
        )

    def test_selects_exact_cj_product_match(self):
        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-123",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://www.etsy.com/listing/123",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        cj_client = Mock()

        cj_client.search_products.return_value = [
            {
                "id": "CJ-WRONG",
                "name": "USB Cable",
            },
            {
                "id": "CJ-CORRECT",
                "name": "Wireless Charger",
            },
            {
                "id": "CJ-OTHER",
                "name": "Phone Stand",
            },
        ]

        pipeline = Mock()

        expected_opportunity = Mock()

        pipeline.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        bridge = EtsyCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        result = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )   

        pipeline.build_opportunity_from_observation.assert_called_once_with(
            supplier=supplier,
            product_id="CJ-CORRECT",
            market_observation=observation,
        )

        self.assertIs(
            result,
            expected_opportunity,
        )

    def test_accepts_similar_cj_product_name(self):
        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-SIMILAR-001",
            name="Wireless Fast Charger 15W",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://www.etsy.com/listing/456",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        cj_client = Mock()

        cj_client.search_products.return_value = [
            {
                "id": "CJ-SIMILAR",
                "name": "15W Wireless Charger",
            },
            {
                "id": "CJ-WRONG",
                "name": "USB Cable",
            },
        ]

        pipeline = Mock()
        expected_opportunity = Mock()

        pipeline.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        bridge = EtsyCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        result = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        pipeline.build_opportunity_from_observation.assert_called_once_with(
            supplier=supplier,
            product_id="CJ-SIMILAR",
            market_observation=observation,
        )

        self.assertIs(
            result,
            expected_opportunity,
        )

    def test_rejects_unrelated_cj_product(self):
        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-NO-MATCH-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://www.etsy.com/listing/789",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        cj_client = Mock()

        cj_client.search_products.return_value = [
            {
                "id": "CJ-WRONG-1",
                "name": "Kitchen Knife Set",
            },
            {
                "id": "CJ-WRONG-2",
                "name": "Garden Watering Hose",
            },
        ]

        pipeline = Mock()

        bridge = EtsyCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        with self.assertRaisesMessage(
            ValueError,
            "No reliable CJ product match found.",
        ):
            bridge.search_and_create_opportunity(
                market_observation=observation,
                supplier=supplier,
            )

        pipeline.build_opportunity_from_observation.assert_not_called()

    def test_selects_cj_product_from_long_personalized_etsy_title(self):
        market_observation = Mock()
        market_observation.name = (
            "Wireless Charger personalisiert mit Holzfront, "
            "individuell mit Gravur, Motiv, Namen, Logo"
        )

        products = [
            {
                "pid": "CJ-001",
                "productNameEn": (
                    "Cross-Border 10W Mirror Wireless Charger "
                    "Fast Charge"
                ),
            },
            {
                "pid": "CJ-002",
                "productNameEn": "USB Cable",
            },
        ]

        service = EtsyCJBridgeService(
            cj_pipeline_service=Mock(),
            cj_client=Mock(),
        )

        product = service.select_best_product(
            market_observation=market_observation,
            products=products,
        )

        self.assertEqual(
            product["pid"],
            "CJ-001",
        )
