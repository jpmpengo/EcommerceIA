from django.test import SimpleTestCase

from product_intelligence.services.supplier_category_matching import (
    SupplierCategoryMatchingService,
)


class SupplierCategoryMatchingServiceTests(
    SimpleTestCase
):

    def test_accepts_relevant_storage_product(
        self,
    ):
        service = (
            SupplierCategoryMatchingService()
        )

        self.assertTrue(
            service.is_relevant(
                product_name=(
                    "Stackable Storage Organizer "
                    "for Small Spaces"
                ),
                search_keyword=(
                    "space saving storage organizer"
                ),
            )
        )

    def test_normalizes_german_diacritics_without_splitting_words(self):
        service = SupplierCategoryMatchingService()
        tokens = service._tokens("faltbarer Laptopständer")
        self.assertIn("laptopstander", tokens)
        self.assertNotIn("laptopst", tokens)
        self.assertNotIn("nder", tokens)

    def test_accepts_french_product_with_localized_alternative_keyword(self):
        service = SupplierCategoryMatchingService()
        self.assertTrue(
            service.is_relevant(
                product_name="Support ordinateur portable pliable réglable aluminium",
                search_keyword="foldable laptop stand",
                alternative_keywords=["support ordinateur portable pliable"],
            )
        )

    def test_accepts_spanish_product_with_localized_alternative_keyword(self):
        service = SupplierCategoryMatchingService()
        self.assertTrue(
            service.is_relevant(
                product_name="Soporte plegable para portátil ajustable de aluminio",
                search_keyword="foldable laptop stand",
                alternative_keywords=["soporte plegable para portátil"],
            )
        )

    def test_accepts_german_inflection_and_compound_word(self):
        service = SupplierCategoryMatchingService()
        self.assertTrue(
            service.is_relevant(
                product_name=(
                    "Laptop Stander Notebook Tisch Halter Tablet Halterung "
                    "Faltbar 7 Winkel Stabil Aluminium"
                ),
                search_keyword="foldable laptop stand",
                alternative_keywords=["faltbarer Laptopständer"],
            )
        )

    def test_accepts_german_product_with_localized_alternative_keyword(self):
        service = SupplierCategoryMatchingService()

        self.assertTrue(
            service.is_relevant(
                product_name=(
                    "Laptop Stander Notebook Tisch Halter Tablet Halterung "
                    "Faltbar 7 Winkel Stabil Aluminium"
                ),
                search_keyword="foldable laptop stand",
                alternative_keywords=["Laptop Stander Faltbar"],
            )
        )

    def test_rejects_unrelated_hair_product(
        self,
    ):
        service = (
            SupplierCategoryMatchingService()
        )

        self.assertFalse(
            service.is_relevant(
                product_name=(
                    "Fake Hair Canvas Head Mold"
                ),
                search_keyword=(
                    "space saving storage organizer"
                ),
            )
        )

    def test_rejects_reusable_pet_pad_for_menstrual_keyword(
        self,
    ):
        service = SupplierCategoryMatchingService()

        self.assertFalse(
            service.is_relevant(
                product_name=(
                    "Non Slip Easy Drying Washable "
                    "And Reusable Pet Changing Pads"
                ),
                search_keyword=(
                    "reusable menstrual pads"
                ),
            )
        )

    def test_rejects_product_missing_bike_anchor(self):
        service = SupplierCategoryMatchingService()
        self.assertFalse(
            service.is_relevant(
                product_name="USB Rechargeable Camping Light",
                search_keyword="USB rechargeable bike light",
            )
        )

    def test_accepts_compact_folding_treadmill(self):
        service = SupplierCategoryMatchingService()
        self.assertTrue(service.is_relevant(product_name="Compact, Quiet Indoor Folding Home Treadmill", search_keyword="compact under desk walking pad treadmill"))

    def test_rejects_unrelated_foot_heating_pad(self):
        service = SupplierCategoryMatchingService()
        self.assertFalse(service.is_relevant(product_name="Office Foot-heating Pad For Warmth Under The Desk", search_keyword="compact under desk walking pad treadmill"))
