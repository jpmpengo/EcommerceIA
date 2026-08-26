from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.cj_supplier_searcher import (
    CJSupplierSearcher,
)


class CJSupplierSearcherTests(
    SimpleTestCase
):

    def test_searches_cj_variants_from_market_observation(
        self,
    ):
        observation = Mock()
        observation.name = "Wireless Charger"

        supplier = Mock()
        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
                "nameEn": "Wireless Charger",
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
            "nameEn": "Wireless Charger",
            "sellPrice": 4.50,
        }

        normalized_product = {
            "external_id": "P1",
            "name": "Wireless Charger",
            "currency": "USD",
            "purchase_price": 4.50,
        }

        client.normalize_product.return_value = (
            normalized_product
        )

        variant = {
            "vid": "V1",
            "pid": "P1",
            "variantNameEn": (
                "Wireless Charger Black"
            ),
            "variantSellPrice": 4.50,
        }

        client.get_product_variants.return_value = [
            variant,
        ]

        client.get_variant_stock.return_value = 100

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            max_offers=3,
        )

        offers = searcher.search_offers(
            market_observation=observation,
        )

        client.search_products.assert_called_once_with(
            keyword="Wireless Charger",
        )

        client.get_product_detail.assert_called_once_with(
            product_id="P1",
        )

        client.normalize_product.assert_called_once_with(
            client.get_product_detail.return_value,
        )

        client.get_product_variants.assert_called_once_with(
            product_id="P1",
        )

        client.get_variant_stock.assert_called_once_with(
            variant_id="V1",
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=supplier,
            product=normalized_product,
            variant=variant,
            stock=100,
            market_observation=observation,
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )

    def test_searches_cj_variants_from_product_idea(
        self,
    ):
        idea = Mock()
        idea.name = (
            "Accessoires de bureau ergonomiques"
        )
        idea.supplier_search_keywords = [
            "ergonomic office accessories",
        ]

        supplier = Mock()
        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
                "nameEn": (
                    "Ergonomic Laptop Stand"
                ),
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
            "nameEn": (
                "Ergonomic Laptop Stand"
            ),
            "sellPrice": 8.50,
        }

        normalized_product = {
            "external_id": "P1",
            "name": (
                "Ergonomic Laptop Stand"
            ),
            "currency": "USD",
            "purchase_price": 8.50,
        }

        client.normalize_product.return_value = (
            normalized_product
        )

        variant = {
            "vid": "V1",
            "pid": "P1",
            "variantNameEn": (
                "Ergonomic Laptop Stand Black"
            ),
            "variantSellPrice": 8.50,
        }

        client.get_product_variants.return_value = [
            variant,
        ]

        client.get_variant_stock.return_value = 100

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        client.search_products.assert_called_once_with(
            keyword=(
                "ergonomic office accessories"
            ),
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=supplier,
            product=normalized_product,
            variant=variant,
            stock=100,
            product_idea=idea,
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )

    def test_rejects_unrelated_cj_product_for_idea(
        self,
    ):
        idea = Mock()
        idea.name = (
            "Rangements modulaires"
        )
        idea.supplier_search_keywords = [
            "space saving storage organizer",
        ]

        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
        }

        client.normalize_product.return_value = {
            "external_id": "P1",
            "name": (
                "Fake Hair Canvas Head Mold"
            ),
            "currency": "USD",
        }

        category_matching_service = Mock()

        category_matching_service.is_relevant.return_value = (
            False
        )

        offer_service = Mock()

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            category_matching_service=(
                category_matching_service
            ),
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        category_matching_service.is_relevant.assert_called_once_with(
            product_name=(
                "Fake Hair Canvas Head Mold"
            ),
            search_keyword=(
                "space saving storage organizer"
            ),
        )

        self.assertEqual(
            offers,
            [],
        )

        client.get_product_variants.assert_not_called()

        offer_service.create_offer_from_variant.assert_not_called()

    def test_keeps_only_one_variant_per_cj_product(
        self,
    ):
        idea = Mock()
        idea.name = "Rangements modulaires"
        idea.supplier_search_keywords = [
            "space saving storage organizer",
        ]

        client = Mock()

        client.search_products.return_value = [
            {
                "id": "P1",
            },
        ]

        client.get_product_detail.return_value = {
            "id": "P1",
        }

        product = {
            "external_id": "P1",
            "name": (
                "Space Saving Storage Organizer"
            ),
            "currency": "USD",
        }

        client.normalize_product.return_value = (
            product
        )

        first_variant = {
            "vid": "V1",
            "variantNameEn": (
                "Storage Organizer Black"
            ),
            "variantSellPrice": "8.50",
        }

        second_variant = {
            "vid": "V2",
            "variantNameEn": (
                "Storage Organizer White"
            ),
            "variantSellPrice": "8.75",
        }

        client.get_product_variants.return_value = [
            first_variant,
            second_variant,
        ]

        client.get_variant_stock.return_value = 100

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )

        offer_service.create_offer_from_variant.assert_called_once_with(
            supplier=searcher.supplier,
            product=product,
            variant=first_variant,
            stock=100,
            product_idea=idea,
        )

        client.get_variant_stock.assert_called_once_with(
            variant_id="V1",
        )

    def test_tries_next_supplier_keyword_when_first_returns_nothing(
        self,
    ):
        idea = Mock()
        idea.name = "Rangements modulaires"
        idea.supplier_search_keywords = [
            "space saving storage organizer",
            "stackable storage box",
        ]

        client = Mock()

        client.search_products.side_effect = [
            [],
            [
                {
                    "id": "P2",
                },
            ],
        ]

        client.get_product_detail.return_value = {
            "id": "P2",
        }

        product = {
            "external_id": "P2",
            "name": "Stackable Storage Box",
            "currency": "USD",
        }

        client.normalize_product.return_value = (
            product
        )

        variant = {
            "vid": "V2",
            "variantNameEn": (
                "Stackable Storage Box"
            ),
            "variantSellPrice": "6.50",
        }

        client.get_product_variants.return_value = [
            variant,
        ]

        client.get_variant_stock.return_value = 75

        expected_offer = Mock()
        offer_service = Mock()

        offer_service.create_offer_from_variant.return_value = (
            expected_offer
        )

        category_matching_service = Mock()
        category_matching_service.is_relevant.return_value = (
            True
        )

        searcher = CJSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            category_matching_service=(
                category_matching_service
            ),
        )

        offers = searcher.search_for_idea(
            product_idea=idea,
        )

        self.assertEqual(
            client.search_products.call_count,
            2,
        )

        client.search_products.assert_any_call(
            keyword=(
                "space saving storage organizer"
            ),
        )

        client.search_products.assert_any_call(
            keyword="stackable storage box",
        )

        self.assertEqual(
            offers,
            [
                expected_offer,
            ],
        )