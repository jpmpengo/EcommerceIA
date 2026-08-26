from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    ComparablePrice,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.comparable_price_qualification import (
    ComparablePriceQualificationService,
)


class ComparablePriceQualificationServiceTests(
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
                    "9-hole Space Saving Hanger"
                ),
                purchase_price=Decimal("0.27"),
                currency="USD",
            )
        )

    def test_retains_complete_positive_price(
        self,
    ):
        comparable_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Cintre pliable à neuf trous"
                ),
                observed_price=Decimal("17.99"),
                currency="EUR",
                source_title=(
                    "Cintre gain de place"
                ),
                source_url=(
                    "https://example.com/hanger"
                ),
                search_query=(
                    "9-hole Space Saving Hanger"
                ),
                evidence=(
                    "Même type de produit, vendu "
                    "à l’unité avec neuf trous."
                ),
            )
        )

        summary = (
            ComparablePriceQualificationService
            .qualify(
                supplier_offer=(
                    self.supplier_offer
                )
            )
        )

        comparable_price.refresh_from_db()

        self.assertEqual(
            comparable_price.qualification_status,
            "retained",
        )

        self.assertEqual(
            comparable_price.qualification_reason,
            (
                "Données indispensables "
                "présentes."
            ),
        )

        self.assertEqual(
            summary,
            {
                "examined": 1,
                "retained": 1,
                "rejected": 0,
            },
        )

    def test_rejects_non_positive_price(
        self,
    ):
        comparable_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Cintre sans prix exploitable"
                ),
                observed_price=Decimal("0.00"),
                currency="EUR",
                source_title=(
                    "Cintre sans prix"
                ),
                source_url=(
                    "https://example.com/no-price"
                ),
                search_query=(
                    "9-hole Space Saving Hanger"
                ),
                evidence=(
                    "Produit similaire."
                ),
            )
        )

        summary = (
            ComparablePriceQualificationService
            .qualify(
                supplier_offer=(
                    self.supplier_offer
                )
            )
        )

        comparable_price.refresh_from_db()

        self.assertEqual(
            comparable_price.qualification_status,
            "rejected",
        )

        self.assertEqual(
            comparable_price.qualification_reason,
            "Prix non positif.",
        )

        self.assertEqual(
            summary,
            {
                "examined": 1,
                "retained": 0,
                "rejected": 1,
            },
        )

    def test_rejects_duplicate_normalized_source_url(
        self,
    ):
        first_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Cintre pliable à neuf trous"
                ),
                observed_price=Decimal("17.99"),
                currency="EUR",
                source_title=(
                    "Cintre gain de place"
                ),
                source_url=(
                    "https://example.com/hanger"
                ),
                search_query=(
                    "9-hole Space Saving Hanger"
                ),
                evidence=(
                    "Même produit vendu à l’unité."
                ),
            )
        )

        duplicate_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Cintre pliable à neuf trous"
                ),
                observed_price=Decimal("17.99"),
                currency="EUR",
                source_title=(
                    "Cintre gain de place"
                ),
                source_url=(
                    "https://example.com/hanger"
                    "?tracking=123"
                ),
                search_query=(
                    "9-hole Space Saving Hanger"
                ),
                evidence=(
                    "Même produit vendu à l’unité."
                ),
            )
        )

        summary = (
            ComparablePriceQualificationService
            .qualify(
                supplier_offer=(
                    self.supplier_offer
                )
            )
        )

        first_price.refresh_from_db()
        duplicate_price.refresh_from_db()

        self.assertEqual(
            first_price.qualification_status,
            "retained",
        )

        self.assertEqual(
            duplicate_price.qualification_status,
            "rejected",
        )

        self.assertEqual(
            duplicate_price.qualification_reason,
            "Source déjà observée.",
        )

        self.assertEqual(
            summary,
            {
                "examined": 2,
                "retained": 1,
                "rejected": 1,
            },
        )