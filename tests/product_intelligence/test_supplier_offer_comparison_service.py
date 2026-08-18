from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    Supplier,
    SupplierOffer,
)

from product_intelligence.services.supplier_offer_comparison import (
    SupplierOfferComparisonService,
)

from product_intelligence.services.supplier_product_matching import (
    SupplierProductMatchingService,
)

from product_intelligence.services.supplier_selection import (
    SupplierSelectionService,
)

from unittest.mock import Mock


class SupplierOfferComparisonServiceTests(TestCase):

    def test_selects_best_offer_among_comparable_products(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        printful = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Gaming Mouse Mat",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=100,
            is_available=True,
        )

        printful_offer = SupplierOffer.objects.create(
            supplier=printful,
            product_name="Gaming Mouse Pad",
            purchase_price=Decimal("9.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=None,
            is_available=True,
        )

        dimensions = {
            cj_offer.id: (450, 400),
            printful_offer.id: (457, 406),
        }

        service = SupplierOfferComparisonService(
            matching_service=(
                SupplierProductMatchingService()
            ),
            selection_service=(
                SupplierSelectionService()
            ),
        )

        best_offer = service.select_best_comparable_offer(
            offers=SupplierOffer.objects.all(),
            target_name="Gaming Mouse Pad",
            target_dimensions=(457, 406),
            dimensions_by_offer=dimensions,
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_ignores_cheaper_offer_when_product_is_not_comparable(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        printful = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Gaming Wireless Mouse",
            purchase_price=Decimal("3.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=100,
            is_available=True,
        )

        printful_offer = SupplierOffer.objects.create(
            supplier=printful,
            product_name="Gaming Mouse Pad",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=None,
            is_available=True,
        )

        service = SupplierOfferComparisonService(
            matching_service=(
                SupplierProductMatchingService()
            ),
            selection_service=(
                SupplierSelectionService()
            ),
        )

        best_offer = service.select_best_comparable_offer(
            offers=SupplierOffer.objects.all(),
            target_name="Gaming Mouse Pad",
        )

        self.assertEqual(
            best_offer,
            printful_offer,
        )

    def test_returns_none_when_no_offer_is_comparable(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Gaming Wireless Mouse",
            purchase_price=Decimal("3.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=100,
            is_available=True,
        )

        service = SupplierOfferComparisonService(
            matching_service=(
                SupplierProductMatchingService()
            ),
            selection_service=(
                SupplierSelectionService()
            ),
        )

        best_offer = service.select_best_comparable_offer(
            offers=SupplierOffer.objects.all(),
            target_name="Gaming Mouse Pad",
        )

        self.assertIsNone(
            best_offer
        )

    def test_selects_best_comparable_offer_across_currencies(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        printful = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Gaming Mouse Mat",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=100,
            is_available=True,
        )

        SupplierOffer.objects.create(
            supplier=printful,
            product_name="Gaming Mouse Pad",
            purchase_price=Decimal("11.72"),
            shipping_cost=Decimal("0.00"),
            currency="USD",
            stock=None,
            is_available=True,
        )

        dimensions = {
            cj_offer.id: (450, 400),
        }

        printful_offer = (
            SupplierOffer.objects.get(
                supplier=printful,
            )
        )

        dimensions[
            printful_offer.id
        ] = (457, 406)

        currency_conversion_service = Mock()

        currency_conversion_service.convert.side_effect = (
            lambda amount,
            from_currency,
            to_currency,
            exchange_rate: (
                amount * exchange_rate
            )
        )

        exchange_rate_client = Mock()
        exchange_rate_client.get_rate.return_value = (
            Decimal("0.86")
        )

        comparison_service = (
            SupplierOfferComparisonService(
                matching_service=(
                    SupplierProductMatchingService()
                ),
                selection_service=(
                    SupplierSelectionService(
                        currency_conversion_service=(
                            currency_conversion_service
                        ),
                        exchange_rate_client=(
                            exchange_rate_client
                        ),
                        target_currency="EUR",
                    )
                ),
            )
        )

        best_offer = (
            comparison_service
            .select_best_comparable_offer(
                offers=(
                    SupplierOffer.objects.all()
                ),
                target_name="Gaming Mouse Pad",
                target_dimensions=(457, 406),
                dimensions_by_offer=dimensions,
            )
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_can_select_printful_when_converted_cost_is_lower(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        printful = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Gaming Mouse Mat",
            purchase_price=Decimal("10.50"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=100,
            is_available=True,
        )

        printful_offer = SupplierOffer.objects.create(
            supplier=printful,
            product_name="Gaming Mouse Pad",
            purchase_price=Decimal("11.72"),
            shipping_cost=Decimal("0.00"),
            currency="USD",
            stock=None,
            is_available=True,
        )

        dimensions = {
            offer.id: dims
            for offer, dims in [
                (
                    SupplierOffer.objects.get(
                        supplier=cj,
                    ),
                    (450, 400),
                ),
                (
                    printful_offer,
                    (457, 406),
                ),
            ]
        }

        currency_conversion_service = Mock()

        currency_conversion_service.convert.side_effect = (
            lambda amount,
            from_currency,
            to_currency,
            exchange_rate: (
                amount * exchange_rate
            )
        )

        exchange_rate_client = Mock()
        exchange_rate_client.get_rate.return_value = (
            Decimal("0.86")
        )

        comparison_service = SupplierOfferComparisonService(
            matching_service=(
                SupplierProductMatchingService()
            ),
            selection_service=(
                SupplierSelectionService(
                    currency_conversion_service=(
                        currency_conversion_service
                    ),
                    exchange_rate_client=(
                        exchange_rate_client
                    ),
                    target_currency="EUR",
                )   
            ),
        )

        best_offer = (
            comparison_service
            .select_best_comparable_offer(
                offers=(
                    SupplierOffer.objects.all()
                ),
                target_name="Gaming Mouse Pad",
                target_dimensions=(457, 406),
                dimensions_by_offer=dimensions,
            )
        )

        self.assertEqual(
            best_offer,
            printful_offer,
        )
