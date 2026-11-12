from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.printful_supplier_searcher import (
    PrintfulSupplierSearcher,
)


class PrintfulSupplierSearcherTests(
    SimpleTestCase
):

    def test_creates_offers_only_from_matching_printful_products(
        self,
    ):
        market_observation = Mock()
        market_observation.name = (
            "Gaming Mouse Pad"
        )

        client = Mock()
        client.get_products.return_value = [
            {
                "id": 583,
                "title": "Gaming Mouse Pad",
            },
            {
                "id": 19,
                "title": "White Glossy Mug",
            },
        ]

        printful_product = {
            "id": 583,
            "title": "Gaming Mouse Pad",
            "currency": "USD",
        }
        variants = [
            {
                "id": 14943,
                "name": (
                    "Gaming Mouse Pad "
                    '(White / 18″×16″)'
                ),
                "price": "11.72",
            },
            {
                "id": 14942,
                "name": (
                    "Gaming Mouse Pad "
                    '(White / 36″×18″)'
                ),
                "price": "19.33",
            },
        ]

        client.get_product.return_value = {
            "product": printful_product,
            "variants": variants,
        }

        matching_service = Mock()
        matching_service.are_products_comparable.side_effect = [
            True,
            False,
        ]

        first_offer = Mock()
        second_offer = Mock()

        offer_service = Mock()
        offer_service.create_offer_from_variant.side_effect = [
            first_offer,
            second_offer,
        ]

        supplier = object()

        searcher = PrintfulSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching_service,
        )

        offers = searcher.search_offers(
            market_observation=market_observation,
        )

        self.assertEqual(
            offers,
            [
                first_offer,
                second_offer,
            ],
        )

        client.get_product.assert_called_once_with(
            product_id=583,
        )

        self.assertEqual(
            offer_service.create_offer_from_variant.call_count,
            2,
        )

        offer_service.create_offer_from_variant.assert_any_call(
            supplier=supplier,
            product=printful_product,
            variant=variants[0],
            supplier_search_keyword="Gaming Mouse Pad",
            market_observation=market_observation,
        )

        offer_service.create_offer_from_variant.assert_any_call(
            supplier=supplier,
            product=printful_product,
            variant=variants[1],
            supplier_search_keyword="Gaming Mouse Pad",
            market_observation=market_observation,
        )

    def test_searches_printful_products_from_product_idea(
        self,
    ):
        idea = Mock()
        idea.name = (
            "Tapis de bureau personnalisables"
        )
        idea.supplier_search_keywords = [
            "custom desk mat",
        ]

        client = Mock()
        client.get_products.return_value = [
            {
                "id": 583,
                "title": "Custom Desk Mat",
            },
        ]

        printful_product = {
            "id": 583,
            "title": "Custom Desk Mat",
            "currency": "USD",
        }

        variant = {
            "id": 14943,
            "name": "Custom Desk Mat 18x16",
            "price": "11.72",
        }

        client.get_product.return_value = {
            "product": printful_product,
            "variants": [
                variant,
            ],
        }

        matching_service = Mock()
        matching_service.are_products_comparable.return_value = (
            True
        )

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        supplier = Mock()

        searcher = PrintfulSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=matching_service,
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        matching_service.are_products_comparable.assert_called_once_with(
            first_name="Custom Desk Mat",
            second_name="custom desk mat",
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=supplier,
            product=printful_product,
            variant=variant,
            supplier_search_keyword="custom desk mat",
            product_idea=idea,
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )
