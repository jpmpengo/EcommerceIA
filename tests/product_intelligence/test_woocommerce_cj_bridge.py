from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.woocommerce_cj_bridge import (
    WooCommerceCJBridgeService,
)


class WooCommerceCJBridgeServiceTests(SimpleTestCase):

    def test_builds_opportunity_from_observation(self):
        cj_client = Mock()
        cj_pipeline_service = Mock()

        observation = Mock()
        observation.name = "Wireless Charger"
        observation.observed_price = Decimal("19.90")
        observation.currency = "EUR"

        cj_client.search_products.return_value = [
            {
                "pid": "CJ-123",
                "productNameEn": "Wireless Charger",
            }
        ]

        expected_opportunity = Mock()

        cj_pipeline_service.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        service = WooCommerceCJBridgeService(
            cj_pipeline_service=cj_pipeline_service,
            cj_client=cj_client,
        )

        opportunity = service.build_opportunity(
            supplier=Mock(),
            market_observation=observation,
        )

        cj_client.search_products.assert_called_once_with(
            keyword="Wireless Charger",
        )

        cj_pipeline_service.build_opportunity_from_observation.assert_called_once()

        self.assertEqual(
            opportunity,
            expected_opportunity,
        )

    def test_returns_none_when_no_cj_product_matches(self):
        cj_client = Mock()
        cj_pipeline_service = Mock()

        observation = Mock()
        observation.name = "Wireless Charger"

        cj_client.search_products.return_value = []

        service = WooCommerceCJBridgeService(
            cj_pipeline_service=cj_pipeline_service,
            cj_client=cj_client,
        )

        opportunity = service.build_opportunity(
            supplier=Mock(),
            market_observation=observation,
        )

        cj_client.search_products.assert_called_once_with(
            keyword="Wireless Charger",
        )

        cj_pipeline_service.build_opportunity_from_observation.assert_not_called()

        self.assertIsNone(opportunity)

    def test_selects_best_matching_cj_product(self):
        cj_client = Mock()
        cj_pipeline_service = Mock()

        observation = Mock()
        observation.name = "Wireless Charger"
        observation.observed_price = Decimal("19.90")
        observation.currency = "EUR"

        supplier = Mock()

        cj_client.search_products.return_value = [
            {
                "pid": "CJ-WRONG-001",
                "productNameEn": "USB Cable",
            },
            {
                "pid": "CJ-BEST-002",
                "productNameEn": "Wireless Charger",
            },
            {
                "pid": "CJ-OTHER-003",
                "productNameEn": "Phone Stand",
            },
        ]

        expected_opportunity = Mock()

        cj_pipeline_service.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        service = WooCommerceCJBridgeService(
            cj_pipeline_service=cj_pipeline_service,
            cj_client=cj_client,
        )

        opportunity = service.build_opportunity(
            supplier=supplier,
            market_observation=observation,
        )

        cj_pipeline_service.build_opportunity_from_observation.assert_called_once_with(
            supplier=supplier,
            product_id="CJ-BEST-002",
            market_observation=observation,
        )

        self.assertIs(
            opportunity,
            expected_opportunity,
        )

    def test_returns_none_when_cj_products_do_not_match(self):
        cj_client = Mock()
        cj_pipeline_service = Mock()

        observation = Mock()
        observation.name = "Wireless Charger"

        supplier = Mock()

        cj_client.search_products.return_value = [
            {
                "pid": "CJ-WRONG-001",
                "productNameEn": "USB Cable",
            },
            {
                "pid": "CJ-WRONG-002",
                "productNameEn": "Phone Stand",
            },
        ]

        service = WooCommerceCJBridgeService(
            cj_pipeline_service=cj_pipeline_service,
            cj_client=cj_client,
        )   

        opportunity = service.build_opportunity(
            supplier=supplier,
            market_observation=observation,
        )

        self.assertIsNone(opportunity)

        cj_pipeline_service.build_opportunity_from_observation.assert_not_called()

    def test_returns_none_when_cj_products_do_not_match(self):
        cj_client = Mock()
        cj_pipeline_service = Mock()

        observation = Mock()
        observation.name = "Wireless Charger"

        supplier = Mock()

        cj_client.search_products.return_value = [
            {
                "pid": "CJ-WRONG-001",
                "productNameEn": "USB Cable",
            },
            {
                "pid": "CJ-WRONG-002",
                "productNameEn": "Phone Stand",
            },
        ]

        service = WooCommerceCJBridgeService(
            cj_pipeline_service=cj_pipeline_service,
            cj_client=cj_client,
        )

        opportunity = service.build_opportunity(
            supplier=supplier,
            market_observation=observation,
        )

        self.assertIsNone(opportunity)

        cj_pipeline_service.build_opportunity_from_observation.assert_not_called()

    def test_selects_reliable_similar_cj_product(self):
        cj_client = Mock()
        cj_pipeline_service = Mock()

        observation = Mock()
        observation.name = "Wireless Charger"
        observation.observed_price = Decimal("19.90")
        observation.currency = "EUR"

        supplier = Mock()

        cj_client.search_products.return_value = [
            {
                "pid": "CJ-WRONG-001",
                "productNameEn": "USB Cable",
            },
            {
                "pid": "CJ-BEST-002",
                "productNameEn": (
                    "Wireless controller charger"
                ),
            },
            {
                "pid": "CJ-WRONG-003",
                "productNameEn": "Phone Stand",
            },
        ]

        expected_opportunity = Mock()

        cj_pipeline_service.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        service = WooCommerceCJBridgeService(
            cj_pipeline_service=cj_pipeline_service,
            cj_client=cj_client,
        )

        opportunity = service.build_opportunity(
            supplier=supplier,
            market_observation=observation,
        )

        cj_pipeline_service.build_opportunity_from_observation.assert_called_once_with(
            supplier=supplier,
            product_id="CJ-BEST-002",
            market_observation=observation,
        )

        self.assertIs(
            opportunity,
            expected_opportunity,
        )