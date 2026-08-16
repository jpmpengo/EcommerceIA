import os
from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from product_intelligence.models import MarketObservation


class RunOpportunityDetectionCommandTests(TestCase):

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "OPPORTUNITY_MINIMUM_MARGIN": "abc",
        },
        clear=True,
    )
    def test_rejects_invalid_minimum_margin(self):
        with self.assertRaisesMessage(
            CommandError,
            "OPPORTUNITY_MINIMUM_MARGIN must be a valid decimal.",
        ):
            call_command(
                "run_opportunity_detection",
            )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "WOOCOMMERCE_BASE_URL": "http://localhost:10004",
            "WOOCOMMERCE_CONSUMER_KEY": "ck_test",
            "WOOCOMMERCE_CONSUMER_SECRET": "cs_test",
        },
        clear=True,
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.WooCommerceCollectionService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.API"
    )
    def test_collects_woocommerce_products_before_detection(
        self,
        api_class,
        collection_service_class,
    ):
        collection_service = Mock()
        collection_service.collect.return_value = []

        collection_service_class.return_value = (
            collection_service
        )

        api_class.return_value = Mock()

        call_command(
            "run_opportunity_detection",
        )

        collection_service.collect.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
        },
        clear=True,
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.WooCommerceCollectionService"
    )
    def test_skips_woocommerce_collection_when_configuration_is_missing(
        self,
        collection_service_class,
    ):
        call_command(
            "run_opportunity_detection",
        )

        collection_service_class.assert_not_called()

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
        },
        clear=True,
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.OpportunityDetectionService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.WooCommerceCJBridgeService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.CJAuthClient"
    )
    def test_injects_woocommerce_bridge_into_detection_service(
        self,
        auth_client_class,
        woocommerce_bridge_class,
        detection_service_class,
    ):
        MarketObservation.objects.create(
            source="woocommerce",
            external_id="WC-COMMAND-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url=(
                "http://localhost:10004/"
                "product/wireless-charger/"
            ),
        )

        auth_client = Mock()
        auth_client.get_access_token.return_value = (
            "test-access-token"
        )
        auth_client_class.return_value = auth_client

        woocommerce_bridge = Mock()
        woocommerce_bridge_class.return_value = (
            woocommerce_bridge
        )

        detection_service = Mock()
        detection_service.process_observations_with_summary.return_value = {
            "processed": 1,
            "created": 0,
            "skipped_no_price": 0,
            "skipped_no_match": 1,
            "skipped_already_processed": 0,
            "results": [],
        }

        detection_service_class.return_value = (
            detection_service
        )

        call_command(
            "run_opportunity_detection",
        )

        woocommerce_bridge_class.assert_called_once()

        kwargs = (
            detection_service_class
            .call_args
            .kwargs
        )

        self.assertIs(
            kwargs["woocommerce_cj_bridge_service"],
            woocommerce_bridge,
        )

        (
            detection_service
            .process_observations_with_summary
            .assert_called_once()
        )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "OPPORTUNITY_MINIMUM_SCORE": "abc",
        },
        clear=True,
    )
    def test_rejects_invalid_minimum_score(self):
        with self.assertRaisesMessage(
            CommandError,
            "OPPORTUNITY_MINIMUM_SCORE must be a valid integer.",
        ):
            call_command(
                "run_opportunity_detection",
            )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "OPPORTUNITY_MINIMUM_SCORE": "120",
        },
        clear=True,
    )
    def test_rejects_minimum_score_outside_valid_range(self):
        with self.assertRaisesMessage(
            CommandError,
            "OPPORTUNITY_MINIMUM_SCORE must be between 0 and 100.",
        ):
            call_command(
                "run_opportunity_detection",
            )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "OPPORTUNITY_MINIMUM_STOCK": "abc",
        },
        clear=True,
    )
    def test_rejects_invalid_minimum_stock(self):
        with self.assertRaisesMessage(
            CommandError,
            "OPPORTUNITY_MINIMUM_STOCK must be a valid integer.",
        ):
            call_command(
                "run_opportunity_detection",
            )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "OPPORTUNITY_MINIMUM_STOCK": "-1",
        },
        clear=True,
    )
    def test_rejects_negative_minimum_stock(self):
        with self.assertRaisesMessage(
            CommandError,
            "OPPORTUNITY_MINIMUM_STOCK must be zero or greater.",
        ):
            call_command(
                "run_opportunity_detection",
            )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "OPPORTUNITY_MINIMUM_SCORE": "60",
        },
        clear=True,
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.SupplierOfferOpportunityService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.OpportunityDecisionService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.CJAuthClient"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.OpportunityDetectionService"
    )
    def test_injects_decision_service_into_opportunity_service(
        self,
        detection_service_class,
        auth_client_class,
        decision_service_class,
        opportunity_service_class,
    ):
        MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-DECISION-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/product",
        )

        auth_client = Mock()
        auth_client.get_access_token.return_value = (
            "test-access-token"
        )
        auth_client_class.return_value = (
            auth_client
        )

        detection_service = Mock()
        detection_service.process_observations_with_summary.return_value = {
            "processed": 1,
            "created": 0,
            "skipped_no_price": 0,
            "skipped_no_match": 1,
            "skipped_already_processed": 0,
            "results": [],
        }

        detection_service_class.return_value = (
            detection_service
        )

        decision_service = Mock()
        decision_service_class.return_value = (
            decision_service
        )

        call_command(
            "run_opportunity_detection",
        )

        decision_service_class.assert_called_once_with(
            minimum_score=60,
        )

        opportunity_service_class.assert_called_once_with(
            minimum_margin=None,
            minimum_score=60,
            minimum_stock=None,
            decision_service=decision_service,
        )
        