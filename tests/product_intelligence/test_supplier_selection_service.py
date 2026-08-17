from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    Supplier,
    SupplierOffer,
)

from product_intelligence.services.supplier_selection import (
    SupplierSelectionService,
)

from unittest.mock import Mock

class SupplierSelectionServiceTests(TestCase):

    def test_selects_cheapest_available_offer(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=20000,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=500,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_ignores_cheapest_offer_when_out_of_stock(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=0,
        )

        bigbuy_offer = SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=500,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )

        self.assertEqual(
            best_offer,
            bigbuy_offer,
        )

    def test_ignores_offer_when_stock_is_unknown(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("6.90"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=None,
        )

        bigbuy_offer = SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=500,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )   

        self.assertEqual(
            best_offer,
            bigbuy_offer,
        )

    def test_selects_offer_with_lowest_total_cost(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("3.50"),
            currency="EUR",
            stock=20000,
        )

        bigbuy_offer = SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=500,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )

        self.assertEqual(
            best_offer,
            bigbuy_offer,
        )

    def test_refuses_to_compare_offers_with_different_currencies_without_conversion(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )   

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("2.00"),
            currency="USD",
            stock=20000,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=500,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Supplier offers must use the same currency.",
        ):
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )

    def test_selects_best_offer_after_currency_conversion(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("2.00"),
            currency="USD",
            stock=20000,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=500,
        )   

        currency_conversion_service = Mock()

        currency_conversion_service.convert.return_value = (
            Decimal("7.998")
        )

        exchange_rate_client = Mock()

        exchange_rate_client.get_rate.return_value = (
            Decimal("0.86")
        )

        service = SupplierSelectionService(
            currency_conversion_service=(
                currency_conversion_service
            ),
            exchange_rate_client=exchange_rate_client,
            target_currency="EUR",
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

        exchange_rate_client.get_rate.assert_called_once_with(
            from_currency="USD",
            to_currency="EUR",
        )

        currency_conversion_service.convert.assert_called_once_with(
            amount=Decimal("9.30"),
            from_currency="USD",
            to_currency="EUR",
            exchange_rate=Decimal("0.86"),
        )

    def test_reuses_exchange_rate_for_same_currency_pair(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger Black",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("2.00"),
            currency="USD",
            stock=100,
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger White",
            purchase_price=Decimal("7.50"),
            shipping_cost=Decimal("2.00"),
            currency="USD",
            stock=100,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("9.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=100,
        )

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

        service = SupplierSelectionService(
            currency_conversion_service=(
                currency_conversion_service
            ),
            exchange_rate_client=exchange_rate_client,
            target_currency="EUR",
        )

        service.select_best_offer(
            SupplierOffer.objects.all()
        )

        exchange_rate_client.get_rate.assert_called_once_with(
            from_currency="USD",
            to_currency="EUR",
        )

    def test_uses_stock_as_tiebreaker_when_total_cost_is_equal(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=20000,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.50"),
            currency="EUR",
            stock=500,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_prefers_higher_stock_even_when_created_second(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.50"),
            currency="EUR",
            stock=500,
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            currency="EUR",
            stock=20000,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )   

    def test_returns_none_when_no_offer_is_eligible(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.30"),
            shipping_cost=Decimal("2.00"),
            currency="EUR",
            stock=0,
        )

        SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("6.90"),
            shipping_cost=Decimal("2.00"),
            currency="EUR",
            stock=None,
        )

        best_offer = (
            SupplierSelectionService.select_best_offer(
                SupplierOffer.objects.all()
            )
        )

        self.assertIsNone(
            best_offer
        )

    def test_ignores_offer_when_shipping_delay_exceeds_maximum(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("6.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=20,
            currency="EUR",
            stock=20000,
        )

        bigbuy_offer = SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("1.00"),
            shipping_days=5,
            currency="EUR",
            stock=500,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            bigbuy_offer,
        )

    def test_ignores_offer_with_unknown_shipping_delay_when_maximum_is_set(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("6.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=None,
            currency="EUR",
            stock=20000,
        )

        bigbuy_offer = SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("1.00"),
            shipping_days=5,
            currency="EUR",
            stock=500,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            bigbuy_offer,
        )

    def test_prefers_lower_cost_when_both_shipping_delays_are_acceptable(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=9,
            currency="EUR",
            stock=20000,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("1.00"),
            shipping_days=3,
            currency="EUR",
            stock=500,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_prefers_faster_shipping_when_total_cost_is_equal(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=8,
            currency="EUR",
            stock=20000,
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.00"),
            shipping_cost=Decimal("2.00"),
            shipping_days=3,
            currency="EUR",
            stock=500,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_prefers_higher_stock_when_total_cost_and_shipping_delay_are_equal(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=5,
            currency="EUR",
            stock=500,
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("7.00"),
            shipping_cost=Decimal("2.00"),
            shipping_days=5,
            currency="EUR",
            stock=20000,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_prefers_offer_shipping_from_target_country_when_cost_is_equal(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=5,
            shipping_country="CN",
            currency="EUR",
            stock=20000,
        )

        bigbuy_offer = SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.50"),
            shipping_days=5,
            shipping_country="FR",
            currency="EUR",
            stock=500,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
            target_shipping_country="FR",
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            bigbuy_offer,
        )

    def test_ignores_shipping_country_when_target_country_is_not_set(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=5,
            shipping_country="CN",
            currency="EUR",
            stock=20000,
        )

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.50"),
            shipping_days=5,
            shipping_country="FR",
            currency="EUR",
            stock=500,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_uses_offer_shipping_country_not_supplier_country(
        self,
    ):
        cj = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bigbuy = Supplier.objects.create(
            name="BigBuy",
            country="ES",
            website="https://www.bigbuy.eu",
            supplier_type="dropshipper",
        )

        cj_offer = SupplierOffer.objects.create(
            supplier=cj,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.00"),
            shipping_cost=Decimal("1.00"),
            shipping_days=5,
            shipping_country="FR",
            currency="EUR",
            stock=500,
        )   

        SupplierOffer.objects.create(
            supplier=bigbuy,
            product_name="Wireless Charger",
            purchase_price=Decimal("8.50"),
            shipping_cost=Decimal("0.50"),
            shipping_days=5,
            shipping_country="ES",
            currency="EUR",
            stock=20000,
        )

        service = SupplierSelectionService(
            target_currency="EUR",
            max_shipping_days=10,
            target_shipping_country="FR",       
        )

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            cj_offer,
        )

    def test_accepts_available_offer_when_stock_quantity_is_unknown(
        self,
    ):
        printful = Supplier.objects.create(
            name="Printful",
            country="US",
            website="https://www.printful.com",
            supplier_type="print_on_demand",
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

        service = SupplierSelectionService()

        best_offer = service.select_best_offer(
            SupplierOffer.objects.all()
        )

        self.assertEqual(
            best_offer,
            printful_offer,
        )