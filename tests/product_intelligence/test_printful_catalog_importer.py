from django.test import TestCase

from product_intelligence.models import Supplier

from product_intelligence.services.printful_catalog_importer import (
    PrintfulCatalogImporter,
)

from decimal import Decimal


class FakePrintfulClient:

    def get_products(
        self,
    ):
        return [
            {
                "id": 583,
                "title": "Gaming Mouse Pad",
            },
        ]

    def get_product(
        self,
        product_id,
    ):
        return {
            "product": {
                "id": product_id,
                "title": "Gaming Mouse Pad",
                "currency": "USD",
            },
            "variants": [
                {
                    "id": 14942,
                    "product_id": product_id,
                    "name": (
                        "Gaming Mouse Pad "
                        "(White / 36″×18″)"
                    ),
                    "size": "36″×18″",
                    "color": "White",
                    "price": "19.33",
                    "in_stock": True,
                },
            ],
        }


class PrintfulCatalogImporterTests(TestCase):

    def test_imports_printful_variants_as_supplier_offers(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        importer = PrintfulCatalogImporter(
            client=FakePrintfulClient(),
            supplier=supplier,
            max_offers=3,
        )

        offers = importer.import_offers()

        self.assertEqual(
            len(offers),
            1,
        )

        offer = offers[0]

        self.assertEqual(
            offer.supplier,
            supplier,
        )

        self.assertEqual(
            offer.supplier_product_id,
            "14942",
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("19.33"),
        )

        self.assertTrue(
            offer.is_available
        )

        self.assertEqual(
            offer.variant_features,
            {
                "dimensions_mm": [
                    914,
                    457,
                ],
                "color": "White",
            },
        )

    def test_respects_max_offers(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        class ClientWithManyVariants:
            def get_products(
                self,
            ):
                return [
                    {
                        "id": 583,
                        "title": "Gaming Mouse Pad",
                    },
                ]

            def get_product(
                self,
                product_id,
            ):
                return {
                    "product": {
                        "id": product_id,
                        "title": "Gaming Mouse Pad",
                        "currency": "USD",
                    },
                    "variants": [
                        {
                            "id": 14941,
                            "product_id": product_id,
                            "name": "Mouse Pad Small",
                            "size": "18″×16″",
                            "color": "White",
                            "price": "11.72",
                            "in_stock": True,
                        },
                        {
                            "id": 14942,
                            "product_id": product_id,
                            "name": "Mouse Pad Large",
                            "size": "36″×18″",
                            "color": "White",
                            "price": "19.33",
                            "in_stock": True,
                        },
                        {
                            "id": 14943,
                            "product_id": product_id,
                            "name": "Mouse Pad Extra",
                            "size": "36″×18″",
                            "color": "Black",
                            "price": "20.00",
                            "in_stock": True,
                        },
                    ],
                }

        importer = PrintfulCatalogImporter(
            client=ClientWithManyVariants(),
            supplier=supplier,
            max_offers=2,
        )

        offers = importer.import_offers()

        self.assertEqual(
            len(offers),
            2,
        )

    def test_ignores_product_without_variants(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        class ClientWithoutVariants:
            def get_products(
                self,
            ):
                return [
                    {
                        "id": 583,
                        "title": "Gaming Mouse Pad",
                    },
                ]

            def get_product(
                self,
                product_id,
            ):
                return {
                    "product": {
                        "id": product_id,
                        "title": "Gaming Mouse Pad",
                        "currency": "USD",
                    },
                    "variants": [],
                }

        importer = PrintfulCatalogImporter(
            client=ClientWithoutVariants(),
            supplier=supplier,
            max_offers=3,
        )

        offers = importer.import_offers()

        self.assertEqual(
            offers,
            [],
        )

