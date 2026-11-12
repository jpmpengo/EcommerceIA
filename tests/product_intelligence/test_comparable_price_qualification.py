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
                "Produit comparable et données "
                "indispensables présentes."
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

    def test_rejects_single_unit_when_supplier_offer_is_pack_of_three(self):
        self.supplier_offer.product_name = "3 high waist physiological pants XL"
        self.supplier_offer.variant_features = {"color": "Gray"}
        self.supplier_offer.save(update_fields=["product_name", "variant_features"])
        comparable_price = ComparablePrice.objects.create(
            supplier_offer=self.supplier_offer,
            product_name="Culotte menstruelle taille haute XL",
            observed_price=Decimal("12.99"),
            currency="EUR",
            source_title="Culotte menstruelle XL",
            source_url="https://example.com/single-pants",
            search_query="physiological pants",
            evidence="Une culotte taille haute en taille XL.",
        )

        summary = ComparablePriceQualificationService.qualify(self.supplier_offer)
        comparable_price.refresh_from_db()

        self.assertEqual(comparable_price.qualification_status, "rejected")
        self.assertIn("quantité", comparable_price.qualification_reason.lower())
        self.assertEqual(summary["retained"], 0)

    def test_retains_same_pack_quantity(self):
        self.supplier_offer.product_name = "Resistance bands set of 5"
        self.supplier_offer.save(update_fields=["product_name"])
        comparable_price = ComparablePrice.objects.create(
            supplier_offer=self.supplier_offer,
            product_name="Lot de 5 bandes de résistance",
            observed_price=Decimal("13.90"),
            currency="EUR",
            source_title="Bandes élastiques lot de 5",
            source_url="https://example.com/five-bands",
            search_query="resistance bands set of 5",
            evidence="Même lot de cinq bandes.",
        )

        ComparablePriceQualificationService.qualify(self.supplier_offer)
        comparable_price.refresh_from_db()

        self.assertEqual(comparable_price.qualification_status, "retained")

    def _qualify_hanging_planter(self, title):
        self.supplier_offer.product_name = (
            "Resin Hanging Planter 15x15x24cm"
        )
        self.supplier_offer.save(update_fields=["product_name"])
        price = ComparablePrice.objects.create(
            supplier_offer=self.supplier_offer,
            product_name=title,
            observed_price=Decimal("19.99"),
            currency="EUR",
            source_title=title,
            source_url=(
                "https://example.com/"
                + str(ComparablePrice.objects.count() + 1)
            ),
            search_query="hanging planter",
            evidence=title,
        )
        ComparablePriceQualificationService.qualify(
            self.supplier_offer
        )
        price.refresh_from_db()
        return price

    def test_retains_hanging_planter_with_same_function(self):
        price = self._qualify_hanging_planter(
            "Macetero colgante para flores 20 cm"
        )
        self.assertEqual(price.qualification_status, "retained")

    def test_rejects_non_hanging_pot(self):
        price = self._qualify_hanging_planter(
            "Pot en forme de cloche 20 cm"
        )
        self.assertEqual(price.qualification_status, "rejected")
        self.assertIn("suspendu", price.qualification_reason)

    def test_rejects_wall_mounted_pot(self):
        price = self._qualify_hanging_planter(
            "Maceta colgante wall dark grey 20 cm"
        )
        self.assertEqual(price.qualification_status, "rejected")
        self.assertIn("murale", price.qualification_reason)

    def test_rejects_self_watering_when_supplier_is_not(self):
        price = self._qualify_hanging_planter(
            "Pot suspendu avec réservoir auto-arrosant"
        )
        self.assertEqual(price.qualification_status, "rejected")
        self.assertIn("auto-arrosage", price.qualification_reason)

    def test_rejects_macrame_hanger_when_comparable_includes_pot(self):
        self.supplier_offer.product_name = "Macrame Pot Holder - Extra Long"
        self.supplier_offer.variant_features = {"product_family": "macrame_hanger", "includes_pot": False}
        self.supplier_offer.save(update_fields=["product_name","variant_features"])
        price = ComparablePrice.objects.create(supplier_offer=self.supplier_offer, product_name="Suspension macrame avec pot ceramique inclus", observed_price=Decimal("29.90"), currency="EUR", source_title="Porte-plante macrame avec pot inclus", source_url="https://example.com/macrame-with-pot", search_query="macrame pot holder", evidence="Ensemble complet comprenant la suspension en macrame et le pot en ceramique.")
        ComparablePriceQualificationService.qualify(self.supplier_offer)
        price.refresh_from_db()
        self.assertEqual(price.qualification_status, "rejected")
        self.assertIn("pot", price.qualification_reason.lower())
