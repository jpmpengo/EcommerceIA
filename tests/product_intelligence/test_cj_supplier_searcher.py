
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.cj_supplier_searcher import (
    CJSupplierSearcher,
)


class CJSupplierSearcherTests(SimpleTestCase):

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
            keyword=idea.name,
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
