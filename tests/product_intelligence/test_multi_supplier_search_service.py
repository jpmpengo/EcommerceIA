from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.multi_supplier_search import (
    MultiSupplierSearchService,
)


class MultiSupplierSearchServiceTests(
    SimpleTestCase
):

    def test_collects_offers_from_all_supplier_searchers(
        self,
    ):
        observation = Mock()
        observation.name = "Gaming Mouse Pad"

        cj_offer = Mock()
        printful_offer = Mock()

        cj_searcher = Mock()
        cj_searcher.search_offers.return_value = [
            cj_offer,
        ]

        printful_searcher = Mock()
        printful_searcher.search_offers.return_value = [
            printful_offer,
        ]

        service = MultiSupplierSearchService(
            supplier_searchers=[
                cj_searcher,
                printful_searcher,
            ]
        )

        offers = service.search(
            market_observation=observation,
        )

        self.assertEqual(
            offers,
            [
                cj_offer,
                printful_offer,
            ],
        )

        cj_searcher.search_offers.assert_called_once_with(
            market_observation=observation,
        )

        printful_searcher.search_offers.assert_called_once_with(
            market_observation=observation,
        )

    def test_skips_supplier_searcher_that_cannot_handle_observation(
        self,
    ):
        observation = Mock()
        observation.name = "Gaming Mouse Pad"

        skipped_searcher = Mock()
        skipped_searcher.can_handle.return_value = False

        active_offer = Mock()

        active_searcher = Mock()
        active_searcher.can_handle.return_value = True
        active_searcher.search_offers.return_value = [
            active_offer,
        ]

        service = MultiSupplierSearchService(
            supplier_searchers=[
                skipped_searcher,
                active_searcher,
            ]
        )

        offers = service.search(
            market_observation=observation,
        )

        self.assertEqual(
            offers,
            [
                active_offer,
            ],
        )

        skipped_searcher.search_offers.assert_not_called()

        active_searcher.search_offers.assert_called_once_with(
            market_observation=observation,
        )
