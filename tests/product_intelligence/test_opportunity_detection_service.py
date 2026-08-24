from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from products.models import Product

from product_intelligence.models import (
    MarketObservation,
    ProductOpportunity,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.opportunity_detection import (
    OpportunityDetectionService,
)


class FakeEbayCJBridgeService:

    def search_and_create_opportunity(
        self,
        market_observation,
        supplier,
    ):
        self.market_observation = market_observation
        self.supplier = supplier

        return {
            "observation_id": market_observation.id,
            "supplier_id": supplier.id,
        }


class OpportunityDetectionServiceTests(TestCase):

    def test_processes_ebay_observation_through_cj_bridge(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-DETECTION-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bridge = FakeEbayCJBridgeService()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=bridge,
        )

        result = service.process_observation(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            bridge.market_observation,
            observation,
        )

        self.assertEqual(
            bridge.supplier,
            supplier,
        )

        self.assertEqual(
            result["observation_id"],
            observation.id,
        )

        self.assertEqual(
            result["supplier_id"],
            supplier.id,
        )

    def test_rejects_non_ebay_observation(self):
        observation = MarketObservation.objects.create(
            source="amazon",
            external_id="AMAZON-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bridge = FakeEbayCJBridgeService()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=bridge,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported market observation source.",
        ):
            service.process_observation(
                market_observation=observation,
                supplier=supplier,
            )

        self.assertFalse(
            hasattr(
                bridge,
                "market_observation",
            )
        )

    def test_rejects_ebay_observation_without_price(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-NO-PRICE-001",
            name="Wireless Charger",
            observed_price=None,
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        bridge = FakeEbayCJBridgeService()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=bridge,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Market observation must have an observed price.",
        ):
            service.process_observation(
                market_observation=observation,
                supplier=supplier,
            )

        self.assertFalse(
            hasattr(
                bridge,
                "market_observation",
            )
        )

    def test_returns_none_when_no_reliable_cj_match_exists(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-NO-MATCH-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        class NoMatchBridge:

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                raise ValueError(
                    "No reliable CJ product match found."
                )

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=NoMatchBridge(),
        )

        result = service.process_observation(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertIsNone(result)

    def test_processes_multiple_observations_and_skips_no_match(self):
        observation_1 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-BATCH-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/product-1",
        )

        observation_2 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-BATCH-002",
            name="Unknown Product",
            observed_price=Decimal("29.90"),
            currency="EUR",
            product_url="https://example.com/product-2",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        class BatchBridge:

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                if (
                    market_observation.external_id
                    == "EBAY-BATCH-002"
                ):
                    raise ValueError(
                        "No reliable CJ product match found."
                    )

                return {
                    "observation_id": market_observation.id,
                    "supplier_id": supplier.id,
                }

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=BatchBridge(),
        )

        results = service.process_observations(
            market_observations=[
                observation_1,
                observation_2,
            ],
            supplier=supplier,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["observation_id"],
            observation_1.id,
        )

        self.assertEqual(
            results[0]["supplier_id"],
            supplier.id,
        )

    def test_processes_batch_and_skips_observation_without_price(self):
        observation_1 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-BATCH-PRICE-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/product-1",
        )

        observation_2 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-BATCH-PRICE-002",
            name="Wireless Charger Without Price",
            observed_price=None,
            currency="EUR",
            product_url="https://example.com/product-2",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        class BatchBridge:

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                return {
                    "observation_id": market_observation.id,
                    "supplier_id": supplier.id,
                }

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=BatchBridge(),
        )

        results = service.process_observations(
            market_observations=[
                observation_1,
                observation_2,
            ],
            supplier=supplier,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["observation_id"],
            observation_1.id,
        )

    def test_returns_batch_summary(self):
        observation_1 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-SUMMARY-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/product-1",
        )

        observation_2 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-SUMMARY-002",
            name="No Price Product",
            observed_price=None,
            currency="EUR",
            product_url="https://example.com/product-2",
        )

        observation_3 = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-SUMMARY-003",
            name="Unknown Product",
            observed_price=Decimal("29.90"),
            currency="EUR",
            product_url="https://example.com/product-3",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        class SummaryBridge:

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                if (
                    market_observation.external_id
                    == "EBAY-SUMMARY-003"
                ):
                    raise ValueError(
                        "No reliable CJ product match found."
                    )

                return {
                    "observation_id": market_observation.id,
                    "supplier_id": supplier.id,
                }

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=SummaryBridge(),
        )

        summary = service.process_observations_with_summary(
            market_observations=[
                observation_1,
                observation_2,
                observation_3,
            ],
            supplier=supplier,
        )

        self.assertEqual(
            summary["processed"],
            3,
        )

        self.assertEqual(
            summary["created"],
            1,
        )

        self.assertEqual(
            summary["skipped_no_price"],
            1,
        )

        self.assertEqual(
            summary["skipped_no_match"],
            1,
        )

        self.assertEqual(
            len(summary["results"]),
            1,
        )

    def test_skips_observation_already_processed_for_supplier(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-ALREADY-PROCESSED-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=supplier,
            market_observation=observation,
            product_name="Wireless Charger",
            purchase_price=Decimal("4.42"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=100,
        )

        class CountingBridge:

            def __init__(self):
                self.call_count = 0

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                self.call_count += 1

                return {
                    "observation_id": market_observation.id,
                }

        bridge = CountingBridge()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=bridge,
        )

        result = service.process_observation(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertIsNone(result)

        self.assertEqual(
            bridge.call_count,
            0,
        )

    def test_batch_summary_counts_already_processed_observation(self):
        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-SUMMARY-PROCESSED-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        SupplierOffer.objects.create(
            supplier=supplier,
            market_observation=observation,
            product_name="Wireless Charger",
            purchase_price=Decimal("4.42"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=20000,
        )

        class CountingBridge:

            def __init__(self):
                self.call_count = 0

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                self.call_count += 1

                return {
                    "observation_id": market_observation.id,
                }

        bridge = CountingBridge()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=bridge,
        )

        summary = service.process_observations_with_summary(
            market_observations=[
                observation,
            ],
            supplier=supplier,
        )

        self.assertEqual(
            summary["processed"],
            1,
        )

        self.assertEqual(
            summary["created"],
            0,
        )

        self.assertEqual(
            summary["skipped_already_processed"],
            1,
        )

        self.assertEqual(
            summary["skipped_no_match"],
            0,
        )

        self.assertEqual(
            summary["results"],
            [],
        )

        self.assertEqual(
            bridge.call_count,
            0,
        )

    def test_processes_etsy_observation_through_etsy_bridge(self):
        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-DETECTION-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url=(
                "https://www.etsy.com/listing/"
                "123456789"
            ),
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        class FakeEtsyCJBridgeService:

            def search_and_create_opportunity(
                self,
                market_observation,
                supplier,
            ):
                self.market_observation = market_observation
                self.supplier = supplier

                return {
                    "observation_id": market_observation.id,
                    "supplier_id": supplier.id,
                }

        etsy_bridge = FakeEtsyCJBridgeService()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=FakeEbayCJBridgeService(),
            etsy_cj_bridge_service=etsy_bridge,
        )

        result = service.process_observation(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            etsy_bridge.market_observation,
            observation,
        )

        self.assertEqual(
            etsy_bridge.supplier,
            supplier,
        )

        self.assertEqual(
            result["observation_id"],
            observation.id,
        )

    def test_rejects_woocommerce_observation_as_unsupported_source(
        self,
    ):
        observation = MarketObservation.objects.create(
            source="woocommerce",
            external_id="WC-DETECTION-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url=(
                "http://localhost:10004/"
                "product/wireless-charger/"
            ),
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=(
                FakeEbayCJBridgeService()
            ),
        )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Unsupported market observation "
                "source."
            ),
        ):
            service.process_observation(
                market_observation=observation,
                supplier=supplier,
            )

    def test_reprocesses_already_processed_observation_when_product_is_out_of_stock(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-RESTOCK-001",
            name="Wireless Charger",
            observed_price=Decimal("27.90"),
            currency="EUR",
        )

        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        old_offer = SupplierOffer.objects.create(
            supplier=supplier,
            market_observation=observation,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=100,
        )

        ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            supplier_offer=old_offer,
            status="published",
            published_product=product,
        )

        bridge = Mock()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=Mock(),
            etsy_cj_bridge_service=bridge,
        )

        new_opportunity = ProductOpportunity(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            restock_product=product,
        )

        bridge.search_and_create_opportunity.return_value = (
            new_opportunity
        )

        result = service.process_observation(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertEqual(
            result,
            new_opportunity,
        )

        bridge.search_and_create_opportunity.assert_called_once_with(
            market_observation=observation,
            supplier=supplier,
        )

    def test_does_not_reprocess_already_processed_observation_when_product_has_stock(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-RESTOCK-STOCKED-001",
            name="Wireless Charger",
            observed_price=Decimal("27.90"),
            currency="EUR",
        )

        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=10,
            is_available=True,
        )

        old_offer = SupplierOffer.objects.create(
            supplier=supplier,
            market_observation=observation,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=100,
        )

        ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            supplier_offer=old_offer,
            status="restocked",
            restock_product=product,
        )

        bridge = Mock()

        service = OpportunityDetectionService(
            ebay_cj_bridge_service=Mock(),
            etsy_cj_bridge_service=bridge,
        )

        result = service.process_observation(
            market_observation=observation,
            supplier=supplier,
        )

        self.assertIsNone(result)

        bridge.search_and_create_opportunity.assert_not_called()

        

