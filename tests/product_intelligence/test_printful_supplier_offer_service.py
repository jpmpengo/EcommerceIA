from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    Supplier,
)

from product_intelligence.services.printful_supplier_offer import (
    PrintfulSupplierOfferService,
)


class PrintfulSupplierOfferServiceTests(TestCase):

    def test_creates_supplier_offer_from_printful_variant(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        product = {
            "id": 583,
            "title": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "id": 14943,
            "product_id": 583,
            "name": (
                'Gaming Mouse Pad '
                '(White / 18"x16")'
            ),
            "price": "11.72",
        }

        service = (
            PrintfulSupplierOfferService()
        )

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        self.assertEqual(
            offer.supplier,
            supplier,
        )

        self.assertEqual(
            offer.supplier_product_id,
            "14943",
        )

        self.assertEqual(
            offer.product_name,
            (
                'Gaming Mouse Pad '
                '(White / 18"x16")'
            ),
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("11.72"),
        )

        self.assertEqual(
            offer.currency,
            "USD",
        )

        self.assertIsNone(
            offer.stock
        )

    def test_create_offer_keeps_printful_variant_image(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        product = {
            "id": 583,
            "title": "Gaming Mouse Pad",
            "currency": "USD",
            "image": (
                "https://example.com/"
                "product-image.jpg"
            ),
        }

        variant = {
            "id": 14943,
            "product_id": 583,
            "name": (
                'Gaming Mouse Pad '
                '(White / 18"x16")'
            ),
            "price": "11.72",
            "image": (
                "https://example.com/"
                "variant-image.jpg"
            ),
            "in_stock": True,
        }

        service = PrintfulSupplierOfferService()

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        self.assertEqual(
            offer.image_url,
            (
                "https://example.com/"
                "variant-image.jpg"
            ),
        )

    def test_create_offer_keeps_printful_availability(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        product = {
            "id": 583,
            "title": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "id": 14943,
            "product_id": 583,
            "name": (
                'Gaming Mouse Pad '
                '(White / 18"x16")'
            ),
            "price": "11.72",
            "in_stock": True,
        }

        service = PrintfulSupplierOfferService()

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        self.assertTrue(
            offer.is_available
        )

        self.assertIsNone(
            offer.stock
        )
