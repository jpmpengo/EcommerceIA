from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.market_price_reference import (
    MarketPriceReferenceService,
)


class MarketPriceReferenceServiceTests(
    SimpleTestCase
):

    def setUp(self):
        self.summary = {
            "minimum_price": Decimal("10.62"),
            "median_price": Decimal("16.21"),
            "maximum_price": Decimal("17.99"),
        }

    def test_selects_minimum_price(
        self,
    ):
        selected_price = (
            MarketPriceReferenceService.select(
                summary=self.summary,
                policy="minimum",
            )
        )

        self.assertEqual(
            selected_price,
            Decimal("10.62"),
        )

    def test_selects_median_price(
        self,
    ):
        selected_price = (
            MarketPriceReferenceService.select(
                summary=self.summary,
                policy="median",
            )
        )

        self.assertEqual(
            selected_price,
            Decimal("16.21"),
        )

    def test_selects_maximum_price(
        self,
    ):
        selected_price = (
            MarketPriceReferenceService.select(
                summary=self.summary,
                policy="maximum",
            )
        )

        self.assertEqual(
            selected_price,
            Decimal("17.99"),
        )

    def test_rejects_unknown_policy(
        self,
    ):
        with self.assertRaisesMessage(
            ValueError,
            (
                "Politique de prix de "
                "référence inconnue."
            ),
        ):
            MarketPriceReferenceService.select(
                summary=self.summary,
                policy="average",
            )

    def test_rejects_missing_reference_price(
        self,
    ):
        summary = {
            "minimum_price": None,
            "median_price": None,
            "maximum_price": None,
        }

        with self.assertRaisesMessage(
            ValueError,
            (
                "Prix de référence "
                "indisponible."
            ),
        ):
            MarketPriceReferenceService.select(
                summary=summary,
                policy="minimum",
            )