from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    ComparablePrice,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.comparable_price_persistence import (
    ComparablePricePersistenceService,
)


class ComparablePricePersistenceServiceTests(
    TestCase
):

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        self.supplier_offer = (
            SupplierOffer.objects.create(
                supplier=self.supplier,
                product_name=(
                    "Stackable Storage Box"
                ),
                purchase_price=Decimal("8.50"),
                currency="USD",
            )
        )

    def test_saves_comparable_prices(
        self,
    ):
        results = [
            {
                "product_name": (
                    "Boîte de rangement empilable"
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
                    "Même fonction et format proche."
                ),
            },
        ]

        saved_prices = (
            ComparablePricePersistenceService.save(
                supplier_offer=(
                    self.supplier_offer
                ),
                results=results,
                search_query=(
                    "Stackable Storage Box"
                ),
                model_name="test-model",
            )
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
            comparable_price.observed_price,
            Decimal("24.90"),
        )

        self.assertEqual(
            comparable_price.currency,
            "EUR",
        )

        self.assertEqual(
            comparable_price.search_query,
            "Stackable Storage Box",
        )

        self.assertEqual(
            comparable_price.model_name,
            "test-model",
        )

    def test_does_not_duplicate_source_url_for_same_offer(
        self,
    ):
        results = [
            {
                "product_name": "Boîte empilable",
                "observed_price": "24.90",
                "currency": "EUR",
                "source_title": (
                    "Boîte de rangement"
                ),
                "source_url": (
                    "https://example.com/box"
                ),
                "evidence": (
                    "Produit comparable."
                ),
            },
        ]

        for _ in range(2):
            ComparablePricePersistenceService.save(
                supplier_offer=(
                    self.supplier_offer
                ),
                results=results,
                search_query=(
                    "Stackable Storage Box"
                ),
                model_name="test-model",
            )

        self.assertEqual(
            ComparablePrice.objects.count(),
            1,
        )

    def test_saves_at_most_five_comparable_prices(
        self,
    ):
        results = [
            {
                "product_name": (
                    f"Boîte comparable {number}"
                ),
                "observed_price": (
                    str(20 + number)
                ),
                "currency": "EUR",
                "source_title": (
                    f"Source {number}"
                ),
                "source_url": (
                    "https://example.com/"
                    f"box-{number}"
                ),
                "evidence": (
                    "Produit comparable."
                ),
            }
            for number in range(
                1,
                8,
            )
        ]

        saved_prices = (
            ComparablePricePersistenceService.save(
                supplier_offer=(
                    self.supplier_offer
                ),
                results=results,
                search_query=(
                    "Stackable Storage Box"
                ),
                model_name="test-model",
            )
        )

        self.assertEqual(
            len(saved_prices),
            5,
        )

        self.assertEqual(
            ComparablePrice.objects.count(),
            5,
        )