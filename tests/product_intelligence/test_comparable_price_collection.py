from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.models import (
    ComparablePrice,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.comparable_price_collection import (
    ComparablePriceCollectionService,
)


class ComparablePriceCollectionServiceTests(
    TestCase
):

    def setUp(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        self.supplier_offer = (
            SupplierOffer.objects.create(
                supplier=supplier,
                product_name=(
                    "Stackable Storage Box"
                ),
                purchase_price=Decimal("8.50"),
                currency="USD",
            )
        )

    def test_searches_and_saves_comparable_prices(
        self,
    ):
        search_service = Mock()

        search_service.search.return_value = {
            "comparables": [
                {
                    "product_name": (
                        "Boîte de rangement "
                        "empilable"
                    ),
                    "observed_price": "24.90",
                    "currency": "EUR",
                    "source_title": (
                        "Boîte empilable blanche"
                    ),
                    "source_url": (
                        "https://example.com/box"
                    ),
                    "evidence": (
                        "Même fonction et "
                        "format comparable."
                    ),
                },
            ],
        }

        service = (
            ComparablePriceCollectionService(
                search_service=search_service,
                model_name="test-model",
            )
        )

        saved_prices = service.collect(
            supplier_offer=(
                self.supplier_offer
            )
        )

        search_service.search.assert_called_once_with(
            self.supplier_offer
        )

        self.assertEqual(
            len(saved_prices),
            1,
        )

        comparable_price = (
            ComparablePrice.objects.get()
        )

        self.assertEqual(
            comparable_price.supplier_offer,
            self.supplier_offer,
        )

        self.assertEqual(
            comparable_price.product_name,
            (
                "Boîte de rangement "
                "empilable"
            ),
        )

        self.assertEqual(
            comparable_price.search_query,
            "Stackable Storage Box",
        )

        self.assertEqual(
            comparable_price.model_name,
            "test-model",
        )

    def test_accepts_empty_search_result(
        self,
    ):
        search_service = Mock()

        search_service.search.return_value = {
            "comparables": [],
        }

        service = (
            ComparablePriceCollectionService(
                search_service=search_service,
                model_name="test-model",
            )
        )

        saved_prices = service.collect(
            supplier_offer=(
                self.supplier_offer
            )
        )

        self.assertEqual(
            saved_prices,
            [],
        )

        self.assertFalse(
            ComparablePrice.objects.exists()
        )