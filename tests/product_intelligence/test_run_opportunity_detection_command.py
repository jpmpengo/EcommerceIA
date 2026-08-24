import os
from decimal import Decimal
from unittest.mock import Mock, call, patch

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

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "ETSY_API_KEY": "test-etsy-key",
            "ETSY_SHARED_SECRET": "test-etsy-secret",
            "ETSY_LISTING_IDS": (
                "1831925561,"
                "1488048002,"
                "1777902778"
            ),
        },
        clear=True,
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.EtsyMarketObservationService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.EtsyClient"
    )
    def test_collects_configured_etsy_listings_before_detection(
        self,
        etsy_client_class,
        observation_service_class,
    ):
        etsy_client = Mock()
        etsy_client.get_listing.side_effect = [
            {"listing_id": 1831925561},
            {"listing_id": 1488048002},
            {"listing_id": 1777902778},
        ]
        etsy_client.normalize_listing.side_effect = [
            {"external_id": "1831925561"},
            {"external_id": "1488048002"},
            {"external_id": "1777902778"},
        ]
        etsy_client_class.return_value = etsy_client

        observation_service = Mock()
        observation_service_class.return_value = (
            observation_service
        )

        call_command(
            "run_opportunity_detection",
        )

        etsy_client.get_listing.assert_has_calls(
            [
                call(listing_id=1831925561),
                call(listing_id=1488048002),
                call(listing_id=1777902778),
            ]
        )

        self.assertEqual(
            etsy_client.normalize_listing.call_count,
            3,
        )

        self.assertEqual(
            observation_service.create_observation.call_count,
            3,
        )

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "test-cj-key",
            "PRINTFUL_API_TOKEN": (
                "test-printful-token"
            ),
            "USE_MULTI_SUPPLIER_PIPELINE": "1",
        },
        clear=True,
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.OpportunityDetectionService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.MarketOpportunityPipelineService"
    )
    @patch(
        "product_intelligence.management.commands."
        "run_opportunity_detection.CJAuthClient"
    )
    def test_uses_multi_supplier_pipeline_when_enabled(
        self,
        auth_client_class,
        market_pipeline_class,
        legacy_detection_service_class,
    ):
        observation = (
            MarketObservation.objects.create(
                source="etsy",
                external_id="WC-MULTI-001",
                name="Gaming Mouse Pad",
                observed_price=Decimal("49.90"),
                currency="EUR",
                product_url=(
                    "http://localhost/product/"
                    "gaming-mouse-pad/"
                ),
            )
        )

        auth_client = Mock()
        auth_client.get_access_token.return_value = (
            "test-access-token"
        )
        auth_client_class.return_value = (
            auth_client
        )

        market_pipeline = Mock()
        market_pipeline.process.return_value = None
        market_pipeline_class.return_value = (
            market_pipeline
        )

        call_command(
            "run_opportunity_detection",
        )

        market_pipeline.process.assert_called_once_with(
            market_observation=observation,
        )

        legacy_detection_service_class.assert_not_called()
        