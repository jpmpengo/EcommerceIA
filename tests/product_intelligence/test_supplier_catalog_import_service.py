from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.supplier_catalog_import import (
    SupplierCatalogImportService,
)


class SupplierCatalogImportServiceTests(
    SimpleTestCase
):

    def test_imports_offers_from_all_suppliers(
        self,
    ):
        cj_offer_1 = object()
        cj_offer_2 = object()
        printful_offer = object()

        cj_importer = Mock()
        cj_importer.import_offers.return_value = [
            cj_offer_1,
            cj_offer_2,
        ]

        printful_importer = Mock()
        printful_importer.import_offers.return_value = [
            printful_offer,
        ]

        service = SupplierCatalogImportService(
            importers=[
                cj_importer,
                printful_importer,
            ]
        )

        offers = service.import_catalog()

        self.assertEqual(
            offers,
            [
                cj_offer_1,
                cj_offer_2,
                printful_offer,
            ],
        )

        cj_importer.import_offers.assert_called_once_with()
        printful_importer.import_offers.assert_called_once_with()

    def test_continues_import_when_one_supplier_fails(
        self,
    ):
        failing_importer = Mock()
        failing_importer.import_offers.side_effect = (
            RuntimeError(
                "Supplier unavailable"
            )
        )

        successful_offer = object()

        successful_importer = Mock()
        successful_importer.import_offers.return_value = [
            successful_offer,
        ]

        service = SupplierCatalogImportService(
            importers=[
                failing_importer,
                successful_importer,
            ]
        )

        offers = service.import_catalog()

        self.assertEqual(
            offers,
            [
                successful_offer,
            ],
        )

        failing_importer.import_offers.assert_called_once_with()
        successful_importer.import_offers.assert_called_once_with()