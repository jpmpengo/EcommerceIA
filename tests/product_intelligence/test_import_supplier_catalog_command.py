from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase


class ImportSupplierCatalogCommandTests(
    TestCase
):

    @patch(
        "product_intelligence.management.commands."
        "import_supplier_catalog."
        "SupplierCatalogImportService"
    )
    def test_command_runs_supplier_catalog_import(
        self,
        service_class,
    ):
        service = Mock()
        service.import_catalog.return_value = [
            object(),
            object(),
        ]

        service_class.return_value = service

        output = StringIO()

        call_command(
            "import_supplier_catalog",
            stdout=output,
        )

        service.import_catalog.assert_called_once_with()

        self.assertIn(
            "2 supplier offers imported",
            output.getvalue(),
        )

    def test_command_accepts_catalog_import_options(
        self,
    ):
        output = StringIO()

        with patch(
            "product_intelligence.management.commands."
            "import_supplier_catalog."
            "SupplierCatalogImportService"
        ) as service_class:
            service = Mock()
            service.import_catalog.return_value = []
            service_class.return_value = service

            call_command(
                "import_supplier_catalog",
                keyword="mouse pad",
                max_offers=3,
                stdout=output,
            )

        self.assertIn(
            "0 supplier offers imported",
            output.getvalue(),
        )

    @patch(
        "product_intelligence.management.commands."
        "import_supplier_catalog."
        "PrintfulCatalogImporter"
    )
    @patch(
        "product_intelligence.management.commands."
        "import_supplier_catalog."
        "CJCatalogImporter"
    )
    @patch(
        "product_intelligence.management.commands."
        "import_supplier_catalog."
        "SupplierCatalogImportService"
    )
    def test_command_builds_cj_and_printful_importers(
        self,
        service_class,
        cj_importer_class,
        printful_importer_class,
    ):
        service = Mock()
        service.import_catalog.return_value = []

        service_class.return_value = service

        call_command(
            "import_supplier_catalog",
            keyword="mouse pad",
            max_offers=3,
        )

        self.assertTrue(
            cj_importer_class.called
        )

        self.assertTrue(
            printful_importer_class.called
        )

        service_class.assert_called_once()

        importers = (
            service_class.call_args.kwargs[
                "importers"
            ]
        )

        self.assertEqual(
            len(importers),
            2,
        )
