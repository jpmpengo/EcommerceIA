from django.test import TestCase

from product_intelligence.models import Supplier

from product_intelligence.services.cj_catalog_importer import (
    CJCatalogImporter,
)


class FakeCJClient:

    def search_products(
        self,
        keyword,
    ):
        return [
            {
                "id": "P1",
                "nameEn": "Gaming Mouse Pad",
            },
        ]

    def get_product_detail(
        self,
        product_id,
    ):
        return {
            "id": product_id,
            "nameEn": "Gaming Mouse Pad",
            "sellPrice": "7.33",
        }

    def normalize_product(
        self,
        product,
    ):
        return {
            "external_id": product["id"],
            "name": product["nameEn"],
            "currency": "USD",
            "purchase_price": product["sellPrice"],
            "product_url": "",
            "image_url": "",
        }

    def get_product_variants(
        self,
        product_id,
    ):
        return [
            {
                "vid": "V1",
                "pid": product_id,
                "variantNameEn": (
                    "Gaming Mouse Pad "
                    "Black 80x40x2cm"
                ),
                "variantSellPrice": "7.33",
            },
        ]

    def get_variant_stock(
        self,
        variant_id,
    ):
        return 100


class CJCatalogImporterTests(TestCase):

    def test_imports_cj_variants_as_supplier_offers(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        importer = CJCatalogImporter(
            client=FakeCJClient(),
            supplier=supplier,
            keyword="mouse pad",
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
            "V1",
        )

        self.assertEqual(
            offer.stock,
            100,
        )

    def test_respects_max_offers(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        client = FakeCJClient()

        client.get_product_variants = lambda product_id: [
            {
                "vid": "V1",
                "pid": product_id,
                "variantNameEn": "Mouse Pad Black 80x40cm",
                "variantSellPrice": "7.33",
            },
            {
                "vid": "V2",
                "pid": product_id,
                "variantNameEn": "Mouse Pad White 80x40cm",
                "variantSellPrice": "7.50",
            },
            {
                "vid": "V3",
                "pid": product_id,
                "variantNameEn": "Mouse Pad Blue 80x40cm",
                "variantSellPrice": "7.80",
            },
        ]

        importer = CJCatalogImporter(
            client=client,
            supplier=supplier,
            keyword="mouse pad",
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
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        client = FakeCJClient()

        client.get_product_variants = (
            lambda product_id: []
        )

        importer = CJCatalogImporter(
            client=client,
            supplier=supplier,
            keyword="mouse pad",
            max_offers=3,
        )

        offers = importer.import_offers()

        self.assertEqual(
            offers,
            [],
        )

