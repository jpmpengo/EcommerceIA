from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.comparable_price_collection_runner import (
    ComparablePriceCollectionRunner,
)


class ComparablePriceCollectionRunnerTests(
    SimpleTestCase
):

    def test_collects_prices_for_every_supplier_offer(
        self,
    ):
        first_offer = Mock()
        second_offer = Mock()

        product_idea = Mock()
        product_idea.supplier_offers.all.return_value = [
            first_offer,
            second_offer,
        ]

        first_prices = [
            Mock(),
            Mock(),
        ]

        second_prices = [
            Mock(),
        ]

        collection_service = Mock()

        collection_service.collect.side_effect = [
            first_prices,
            second_prices,
        ]

        runner = (
            ComparablePriceCollectionRunner(
                collection_service=(
                    collection_service
                )
            )
        )

        summary = runner.run(
            product_idea=product_idea
        )

        self.assertEqual(
            collection_service.collect.call_count,
            2,
        )

        collection_service.collect.assert_any_call(
            supplier_offer=first_offer,
        )

        collection_service.collect.assert_any_call(
            supplier_offer=second_offer,
        )

        self.assertEqual(
            summary,
            {
                "offers_processed": 2,
                "comparable_prices_saved": 3,
            },
        )

    def test_accepts_category_without_supplier_offers(
        self,
    ):
        product_idea = Mock()
        product_idea.supplier_offers.all.return_value = []

        collection_service = Mock()

        runner = (
            ComparablePriceCollectionRunner(
                collection_service=(
                    collection_service
                )
            )
        )

        summary = runner.run(
            product_idea=product_idea
        )

        collection_service.collect.assert_not_called()

        self.assertEqual(
            summary,
            {
                "offers_processed": 0,
                "comparable_prices_saved": 0,
            },
        )