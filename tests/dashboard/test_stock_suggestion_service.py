from django.test import TestCase

from dashboard.services.stock_suggestion_service import (
    StockSuggestionService,
)


class FakeSupplierOffer:
    def __init__(self, stock):
        self.stock = stock


class FakeOpportunity:
    def __init__(self, supplier_offer=None):
        self.supplier_offer = supplier_offer


class StockSuggestionServiceTests(TestCase):

    def test_suggests_maximum_ten_units(self):
        opportunity = FakeOpportunity(
            supplier_offer=FakeSupplierOffer(
                stock=250,
            )
        )

        stock = StockSuggestionService.suggest(
            opportunity
        )

        self.assertEqual(
            stock,
            10,
        )

    def test_suggests_available_stock_when_below_ten(self):
        opportunity = FakeOpportunity(
            supplier_offer=FakeSupplierOffer(
                stock=6,
            )
        )

        stock = StockSuggestionService.suggest(
            opportunity
        )

        self.assertEqual(
            stock,
            6,
        )

    def test_returns_none_without_supplier_offer(self):
        opportunity = FakeOpportunity()

        stock = StockSuggestionService.suggest(
            opportunity
        )

        self.assertIsNone(stock)

    def test_returns_none_when_supplier_stock_is_zero(self):
        opportunity = FakeOpportunity(
            supplier_offer=FakeSupplierOffer(
                stock=0,
            )
        )

        stock = StockSuggestionService.suggest(
            opportunity
        )

        self.assertIsNone(stock)

        