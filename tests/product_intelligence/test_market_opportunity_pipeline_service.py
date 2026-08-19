from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.market_opportunity_pipeline import (
    MarketOpportunityPipelineService,
)


class MarketOpportunityPipelineServiceTests(
    SimpleTestCase
):

    def test_creates_opportunity_from_best_supplier_offer(
        self,
    ):
        market_observation = Mock()
        market_observation.name = (
            "Gaming Mouse Pad"
        )
        market_observation.observed_price = (
            Decimal("29.90")
        )

        cj_offer = Mock()
        printful_offer = Mock()

        supplier_search_service = Mock()
        supplier_search_service.search.return_value = [
            cj_offer,
            printful_offer,
        ]

        comparison_service = Mock()
        comparison_service.select_best_comparable_offer.return_value = (
            cj_offer
        )

        expected_opportunity = object()

        opportunity_service = Mock()
        opportunity_service.create_opportunity.return_value = (
            expected_opportunity
        )

        service = MarketOpportunityPipelineService(
            supplier_search_service=(
                supplier_search_service
            ),
            comparison_service=(
                comparison_service
            ),
            opportunity_service=(
                opportunity_service
            ),
        )

        opportunity = service.process(
            market_observation=(
                market_observation
            ),
        )

        self.assertIs(
            opportunity,
            expected_opportunity,
        )

        supplier_search_service.search.assert_called_once_with(
            market_observation=(
                market_observation
            ),
        )

        comparison_service.select_best_comparable_offer.assert_called_once_with(
            offers=[
                cj_offer,
                printful_offer,
            ],
            target_name=(
                "Gaming Mouse Pad"
            ),
        )

        opportunity_service.create_opportunity.assert_called_once_with(
            offer=cj_offer,
            market_price=Decimal("29.90"),
        )

    def test_returns_none_when_no_comparable_supplier_offer(
        self,
    ):
        market_observation = Mock()
        market_observation.name = (
            "Gaming Mouse Pad"
        )
        market_observation.observed_price = (
            Decimal("29.90")
        )

        supplier_search_service = Mock()
        supplier_search_service.search.return_value = []

        comparison_service = Mock()
        comparison_service.select_best_comparable_offer.return_value = (
            None
        )

        opportunity_service = Mock()

        service = MarketOpportunityPipelineService(
            supplier_search_service=(
                supplier_search_service
            ),
            comparison_service=(
                comparison_service
            ),
            opportunity_service=(
                opportunity_service
            ),
        )

        opportunity = service.process(
            market_observation=(
                market_observation
            ),
        )

        self.assertIsNone(
            opportunity
        )

        opportunity_service.create_opportunity.assert_not_called()

    def test_returns_none_when_market_price_is_missing(
        self,
    ):
        market_observation = Mock()
        market_observation.name = (
            "Gaming Mouse Pad"
        )
        market_observation.observed_price = None

        supplier_search_service = Mock()
        comparison_service = Mock()
        opportunity_service = Mock()

        service = MarketOpportunityPipelineService(
            supplier_search_service=(
                supplier_search_service
            ),
            comparison_service=(
                comparison_service
            ),
            opportunity_service=(
                opportunity_service
            ),
        )

        opportunity = service.process(
            market_observation=(
                market_observation
            ),
        )

        self.assertIsNone(
            opportunity
        )

        supplier_search_service.search.assert_not_called()

        comparison_service.select_best_comparable_offer.assert_not_called()

        opportunity_service.create_opportunity.assert_not_called()

    def test_converts_best_offer_to_market_currency(
        self,
    ):
        market_observation = Mock()
        market_observation.name = (
            "Gaming Mouse Pad"
        )
        market_observation.observed_price = (
            Decimal("49.90")
        )
        market_observation.currency = "EUR"

        best_offer = Mock()
        best_offer.purchase_price = (
            Decimal("10.00")
        )
        best_offer.currency = "USD"

        supplier_search_service = Mock()
        supplier_search_service.search.return_value = [
            best_offer,
        ]

        comparison_service = Mock()
        comparison_service.select_best_comparable_offer.return_value = (
            best_offer
        )

        currency_conversion_service = Mock()
        currency_conversion_service.convert.return_value = (
            Decimal("9.20")
        )

        exchange_rate_client = Mock()
        exchange_rate_client.get_rate.return_value = (
            Decimal("0.92")
        )

        opportunity_service = Mock()

        service = MarketOpportunityPipelineService(
            supplier_search_service=(
                supplier_search_service
            ),
            comparison_service=(
                comparison_service
            ),
            opportunity_service=(
                opportunity_service
            ),
            currency_conversion_service=(
                currency_conversion_service
            ),
            exchange_rate_client=(
                exchange_rate_client
            ),
        )

        service.process(
            market_observation=(
                market_observation
            ),
        )

        exchange_rate_client.get_rate.assert_called_once_with(
            from_currency="USD",
            to_currency="EUR",
        )

        currency_conversion_service.convert.assert_called_once_with(
            amount=Decimal("10.00"),
            from_currency="USD",
            to_currency="EUR",
            exchange_rate=Decimal("0.92"),
        )

        self.assertEqual(
            best_offer.purchase_price,
            Decimal("9.20"),
        )
        self.assertEqual(
            best_offer.currency,
            "EUR",
        )

        best_offer.save.assert_called_once_with(
            update_fields=[
                "purchase_price",
                "currency",
            ]
        )

        opportunity_service.create_opportunity.assert_called_once_with(
            offer=best_offer,
            market_price=Decimal("49.90"),
        )
