from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    ComparablePrice,
    Supplier,
    SupplierOffer,
)


class ComparablePriceQualificationModelTests(
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

    def test_is_collected_by_default(
        self,
    ):
        comparable_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Boîte de rangement empilable"
                ),
                observed_price=Decimal("24.90"),
                currency="EUR",
                source_title=(
                    "Boîte empilable blanche"
                ),
                source_url=(
                    "https://example.com/box"
                ),
                search_query=(
                    "Stackable Storage Box"
                ),
            )
        )

        self.assertEqual(
            comparable_price.qualification_status,
            "collected",
        )

        self.assertEqual(
            comparable_price.qualification_reason,
            "",
        )

    def test_can_be_retained(
        self,
    ):
        comparable_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Boîte de rangement empilable"
                ),
                observed_price=Decimal("24.90"),
                currency="EUR",
                source_title=(
                    "Boîte empilable blanche"
                ),
                source_url=(
                    "https://example.com/box"
                ),
                search_query=(
                    "Stackable Storage Box"
                ),
                qualification_status="retained",
                qualification_reason=(
                    "Produit comparable et "
                    "prix public vérifiable."
                ),
            )
        )

        self.assertEqual(
            comparable_price.qualification_status,
            "retained",
        )

    def test_can_be_rejected_with_reason(
        self,
    ):
        comparable_price = (
            ComparablePrice.objects.create(
                supplier_offer=(
                    self.supplier_offer
                ),
                product_name=(
                    "Lot de dix sacs"
                ),
                observed_price=Decimal("39.90"),
                currency="EUR",
                source_title=(
                    "Lot de sacs"
                ),
                source_url=(
                    "https://example.com/bags"
                ),
                search_query=(
                    "Stackable Storage Box"
                ),
                qualification_status="rejected",
                qualification_reason=(
                    "Lot non comparable au "
                    "produit unitaire."
                ),
            )
        )

        self.assertEqual(
            comparable_price.qualification_status,
            "rejected",
        )

        self.assertEqual(
            comparable_price.qualification_reason,
            (
                "Lot non comparable au "
                "produit unitaire."
            ),
        )