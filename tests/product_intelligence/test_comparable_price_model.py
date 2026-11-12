from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    ComparablePrice,
    Supplier,
    SupplierOffer,
)


class ComparablePriceModelTests(TestCase):

    def test_comparable_price_is_linked_to_supplier_offer(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Fournisseur Test",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name=(
                "Stackable Storage Box"
            ),
            purchase_price=Decimal("6.50"),
            currency="USD",
            stock=75,
        )

        comparable_price = (
            ComparablePrice.objects.create(
                supplier_offer=offer,
                product_name=(
                    "Boîte de rangement empilable"
                ),
                observed_price=Decimal("24.90"),
                currency="EUR",
                source_title=(
                    "Boutique de rangement"
                ),
                source_url=(
                    "https://example.com/"
                    "boite-rangement"
                ),
                search_query=(
                    "boîte rangement empilable prix"
                ),
            )
        )

        self.assertEqual(
            comparable_price.supplier_offer,
            offer,
        )

        self.assertEqual(
            list(
                offer.comparable_prices.all()
            ),
            [
                comparable_price,
            ],
        )

        self.assertIsNotNone(
            comparable_price.observed_at,
        )
    def test_commercial_segment_defaults_to_unclassified(self):
        field = ComparablePrice._meta.get_field("commercial_segment")
        reason_field = ComparablePrice._meta.get_field("commercial_segment_reason")
        self.assertEqual(field.get_default(), "unclassified")
        self.assertTrue(reason_field.null)
        self.assertTrue(reason_field.blank)
