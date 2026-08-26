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