from decimal import Decimal
from uuid import uuid4

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
        is_current=True,
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
            is_current=is_current,
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

        shipping_comparables = summary.pop("shipping_comparables")
        self.assertIsInstance(shipping_comparables, list)
        self.assertEqual(len(shipping_comparables), summary["retained_count"])
        self.assertEqual(
            summary,
            {
                "currency": "EUR",
                "collection_batch_id": None,
                "retained_count": 5,
                "minimum_price": Decimal("10.62"),
                "commercial_median_price": None,
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

        shipping_comparables = summary.pop("shipping_comparables")
        self.assertIsInstance(shipping_comparables, list)
        self.assertEqual(len(shipping_comparables), summary["retained_count"])
        self.assertEqual(
            summary,
            {
                "currency": "EUR",
                "collection_batch_id": None,
                "retained_count": 0,
                "minimum_price": None,
                "commercial_median_price": None,
                "median_price": None,
                "maximum_price": None,
                "source_domain_count": 0,
            },
        )

    def test_returns_current_collection_batch_id(self):
        batch_id = uuid4()
        price = self._create_price(
            "17.63",
            "https://example.com/current-batch",
        )
        price.collection_batch_id = batch_id
        price.save(update_fields=["collection_batch_id"])

        summary = ComparablePriceSummaryService.summarize(
            supplier_offer=self.supplier_offer,
            currency="EUR",
        )

        self.assertEqual(
            summary["collection_batch_id"],
            batch_id,
        )

    def test_ignores_historical_collection_prices(self):
        self._create_price(
            "99.00",
            "https://example.com/historical",
            is_current=False,
        )
        self._create_price(
            "17.63",
            "https://example.com/current",
        )

        summary = ComparablePriceSummaryService.summarize(
            supplier_offer=self.supplier_offer,
            currency="EUR",
        )

        self.assertEqual(summary["retained_count"], 1)
        self.assertEqual(
            summary["median_price"],
            Decimal("17.63"),
        )

    def test_calculates_direct_commercial_median(self):
        for price, segment in [('38.99', 'direct'), ('53.99', 'direct'), ('99.95', 'direct'), ('315.99', 'different_segment')]:
            comparable = self._create_price(price, 'https://example.com/product-' + price)
            comparable.commercial_segment = segment
            comparable.commercial_segment_reason = 'Positionnement documente'
            comparable.save(update_fields=['commercial_segment', 'commercial_segment_reason'])
        summary = ComparablePriceSummaryService.summarize(self.supplier_offer, 'EUR')
        self.assertEqual(summary['median_price'], Decimal('76.97'))
        self.assertEqual(summary['commercial_median_price'], Decimal('53.99'))
