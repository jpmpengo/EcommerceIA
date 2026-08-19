from decimal import Decimal

from django.test import TestCase

from product_intelligence.services.printful_supplier_offer import (
    PrintfulSupplierOfferService,
)

from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)

from product_intelligence.models import (
    MarketObservation,
    Supplier,
    SupplierOffer,
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

    def test_create_offer_stores_variant_features(
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
            "id": 14942,
            "product_id": 583,
            "name": (
                "Gaming Mouse Pad "
                "(White / 36″×18″)"
            ),
            "size": "36″×18″",
            "color": "White",
            "price": "19.33",
            "in_stock": True,
        }

        service = PrintfulSupplierOfferService(
            variant_features_service=(
                VariantFeaturesService()
            ),
        )

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
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

    def test_create_offer_from_variant_updates_existing_offer(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        service = PrintfulSupplierOfferService(
            variant_features_service=(
                VariantFeaturesService()
            ),
        )

        product = {
            "id": 583,
            "title": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "id": 14942,
            "product_id": 583,
            "name": (
                "Gaming Mouse Pad "
                "(White / 36″×18″)"
            ),
            "size": "36″×18″",
            "color": "White",
            "price": "19.33",
            "in_stock": True,
        }

        first_offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        variant["price"] = "18.99"
        variant["in_stock"] = False

        second_offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        self.assertEqual(
            first_offer.id,
            second_offer.id,
        )

        self.assertEqual(
            SupplierOffer.objects.count(),
            1,
        )

        second_offer.refresh_from_db()

        self.assertEqual(
            second_offer.purchase_price,
            Decimal("18.99"),
        )

        self.assertFalse(
            second_offer.is_available,
        )

    def test_keeps_separate_variant_offer_per_market_observation(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        first_observation = MarketObservation.objects.create(
            source="woocommerce",
            external_id="WC-PRINTFUL-001",
            name="Gaming Mouse Pad",
            observed_price=Decimal("49.90"),
            currency="EUR",
            product_url="https://example.com/woo-mouse-pad",
        )

        second_observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-PRINTFUL-001",
            name="Gaming Mouse Pad",
            observed_price=Decimal("51.96"),
            currency="EUR",
            product_url="https://example.com/etsy-mouse-pad",
        )

        service = PrintfulSupplierOfferService()

        product = {
            "id": 583,
            "title": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "id": 14942,
            "product_id": 583,
            "name": "Gaming Mouse Pad (White / 36x18)",
            "price": "19.33",
            "in_stock": True,
        }

        first_offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            market_observation=first_observation,
        )

        second_offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            market_observation=second_observation,
        )

        self.assertNotEqual(
            first_offer.id,
            second_offer.id,
        )

        self.assertEqual(
            SupplierOffer.objects.count(),
            2,
        )

        self.assertEqual(
            first_offer.market_observation,
            first_observation,
        )

        self.assertEqual(
            second_offer.market_observation,
            second_observation,
        )
