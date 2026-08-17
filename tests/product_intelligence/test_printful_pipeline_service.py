from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    Supplier,
)

from product_intelligence.services.printful_pipeline import (
    PrintfulPipelineService,
)

from product_intelligence.services.printful_supplier_offer import (
    PrintfulSupplierOfferService,
)


class FakePrintfulClient:

    def get_product(
        self,
        product_id,
    ):
        return {
            "product": {
                "id": 583,
                "title": "Gaming Mouse Pad",
                "currency": "USD",
                "image": (
                    "https://example.com/"
                    "product.jpg"
                ),
            },
            "variants": [
                {
                    "id": 14943,
                    "product_id": 583,
                    "name": (
                        'Gaming Mouse Pad '
                        '(White / 18"x16")'
                    ),
                    "price": "11.72",
                    "image": (
                        "https://example.com/"
                        "variant.jpg"
                    ),
                    "in_stock": True,
                }
            ],
        }


class PrintfulPipelineServiceTests(TestCase):

    def test_builds_supplier_offer_from_printful_product(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        service = PrintfulPipelineService(
            client=FakePrintfulClient(),
            offer_service=(
                PrintfulSupplierOfferService()
            ),
        )

        offer = service.build_supplier_offer(
            supplier=supplier,
            product_id=583,
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

        self.assertTrue(
            offer.is_available
        )

    def test_refuses_product_without_variants(
        self,
    ):
        class PrintfulClientWithoutVariants:
            def get_product(
                self,
                product_id,
            ):
                return {
                    "product": {
                        "id": 583,
                        "title": "Gaming Mouse Pad",
                        "currency": "USD",
                    },
                    "variants": [],
                }

        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        service = PrintfulPipelineService(
            client=PrintfulClientWithoutVariants(),
            offer_service=(
                PrintfulSupplierOfferService()
            ),
        )

        with self.assertRaisesMessage(
            ValueError,
            "Printful product has no variants.",
        ):
            service.build_supplier_offer(
                supplier=supplier,
                product_id=583,
            )