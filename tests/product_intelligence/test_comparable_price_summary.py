from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import (
    ComparablePrice,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.comparable_price_summary import (
    ComparablePriceSummaryService,
)


class ComparablePriceSummaryServiceTests(
    TestCase
):

    def setUp(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        self.supplier_offer = (
            SupplierOffer.objects.create(
                supplier=supplier,
                product_name=(
                    "9-hole Space Saving Hanger"
                ),
                purchase_price=Decimal("0.27"),
                currency="USD",
            )
        )

    def _create_price(
        self,
        price,
        url,
        status="retained",
    ):
        return ComparablePrice.objects.create(
            supplier_offer=(
                self.supplier_offer
            ),
            product_name=(
                "Cintre pliable à neuf trous"
            ),
            observed_price=Decimal(price),
            currency="EUR",
            source_title=(
                "Cintre gain de place"
            ),
            source_url=url,
            search_query=(
                "9-hole Space Saving Hanger"
            ),
            evidence=(
                "Même type de produit."
            ),
            qualification_status=status,
        )

    def test_summarizes_retained_prices(
        self,
    ):
        self._create_price(
            "17.99",
            "https://www.manomano.fr/product-1",
        )

        self._create_price(
            "11.55",
            "https://www.fruugo.fr/product-2",
        )

        self._create_price(
            "17.99",
            "https://www.leroymerlin.fr/product-3",
        )

        self._create_price(
            "10.62",
            "https://www.manomano.es/product-4",
        )

        self._create_price(
            "16.21",
            "https://www.manomano.es/product-5",
        )

        summary = (
            ComparablePriceSummaryService
            .summarize(
                supplier_offer=(
                    self.supplier_offer
                ),
                currency="EUR",
            )
        )

        self.assertEqual(
            summary,
            {
                "currency": "EUR",
                "retained_count": 5,
                "minimum_price": Decimal("10.62"),
                "median_price": Decimal("16.21"),
                "maximum_price": Decimal("17.99"),
                "source_domain_count": 4,
            },
        )

    def test_ignores_rejected_prices(
        self,
    ):
        self._create_price(
            "15.00",
            "https://example.com/valid",
        )

        self._create_price(
            "1.00",
            "https://example.net/rejected",
            status="rejected",
        )

        summary = (
            ComparablePriceSummaryService
            .summarize(
                supplier_offer=(
                    self.supplier_offer
                ),
                currency="EUR",
            )
        )

        self.assertEqual(
            summary["retained_count"],
            1,
        )

        self.assertEqual(
            summary["minimum_price"],
            Decimal("15.00"),
        )

        self.assertEqual(
            summary["median_price"],
            Decimal("15.00"),
        )

        self.assertEqual(
            summary["maximum_price"],
            Decimal("15.00"),
        )

    def test_returns_empty_summary_without_retained_price(
        self,
    ):
        summary = (
            ComparablePriceSummaryService
            .summarize(
                supplier_offer=(
                    self.supplier_offer
                ),
                currency="EUR",
            )
        )

        self.assertEqual(
            summary,
            {
                "currency": "EUR",
                "retained_count": 0,
                "minimum_price": None,
                "median_price": None,
                "maximum_price": None,
                "source_domain_count": 0,
            },
        )