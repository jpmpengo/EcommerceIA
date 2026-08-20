from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)
from product_intelligence.services.etsy_client import EtsyClient
from product_intelligence.services.etsy_market_observation import (
    EtsyMarketObservationService,
)
from product_intelligence.services.etsy_cj_bridge import (
    EtsyCJBridgeService,
)


class EtsyCJIntegrationTests(TestCase):

    def test_etsy_listing_flows_to_cj_pipeline(self):
        # 1. Donnée brute simulée provenant d'Etsy
        raw_listing = {
            "listing_id": 123456789,
            "title": "Wireless Charger",
            "price": {
                "amount": 1990,
                "divisor": 100,
                "currency_code": "EUR",
            },
            "url": "https://www.etsy.com/listing/123456789",
        }

        # 2. Normalisation Etsy
        etsy_client = EtsyClient(
            api_key="test-etsy-key",
            shared_secret="test-etsy-secret",
            http_client=None,
        )

        normalized = etsy_client.normalize_listing(
            raw_listing
        )

        # 3. Création de MarketObservation
        observation_service = EtsyMarketObservationService()

        observation = observation_service.create_observation(
            listing=normalized,
        )

        self.assertIsInstance(
            observation,
            MarketObservation,
        )

        self.assertEqual(
            observation.source,
            "etsy",
        )

        self.assertEqual(
            observation.observed_price,
            Decimal("19.90"),
        )

        # 4. Fournisseur CJ
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        # 5. Réponse CJ simulée
        cj_client = Mock()

        cj_client.search_products.return_value = [
            {
                "id": "CJ-ETSY-001",
                "name": "Wireless Charger",
            }
        ]

        # 6. Pipeline CJ simulé
        pipeline = Mock()

        expected_opportunity = Mock()

        pipeline.build_opportunity_from_observation.return_value = (
            expected_opportunity
        )

        bridge = EtsyCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        # 7. Etsy -> CJ
        opportunity = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        # 8. Vérifications
        cj_client.search_products.assert_called_once_with(
            keyword="Wireless Charger",
        )

        pipeline.build_opportunity_from_observation.assert_called_once_with(
            supplier=supplier,
            product_id="CJ-ETSY-001",
            market_observation=observation,
        )

        self.assertIs(
            opportunity,
            expected_opportunity,
        )

    def test_etsy_listing_creates_supplier_offer_and_product_opportunity(self):
        from product_intelligence.services.cj_pipeline import (
            CJPipelineService,
        )
        from product_intelligence.services.cj_supplier_offer import (
            CJSupplierOfferService,
        )
        from product_intelligence.services.currency_conversion import (
            CurrencyConversionService,
        )
        from product_intelligence.services.supplier_offer_opportunity import (
            SupplierOfferOpportunityService,
        )

        raw_listing = {
            "listing_id": 987654321,
            "title": "Wireless Charger",
            "price": {
                "amount": 1990,
                "divisor": 100,
                "currency_code": "EUR",
            },
            "url": "https://www.etsy.com/listing/987654321",
        }

        etsy_client = EtsyClient(
            api_key="test-etsy-key",
            shared_secret="test-etsy-secret",
            http_client=None,
        )

        normalized_listing = etsy_client.normalize_listing(
            raw_listing
        )

        observation = EtsyMarketObservationService().create_observation(
            listing=normalized_listing,
        )

        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        class FakeCJClient:

            def search_products(self, keyword):
                return [
                    {
                        "id": "CJ-ETSY-REAL-001",
                        "name": "Wireless Charger",
                    }
                ]

            def get_product_detail(self, product_id):
                return {
                    "pid": product_id,
                    "productNameEn": "Wireless Charger",
                    "sellPrice": "5.10",
                }

            def normalize_product(self, product):
                return {
                    "external_id": product["pid"],
                    "name": product["productNameEn"],
                    "purchase_price": product["sellPrice"],
                    "currency": "USD",
                }

            def get_product_variants(self, product_id):
                return [
                    {
                        "vid": "ETSY-VARIANT-001",
                        "pid": product_id,
                        "variantNameEn": "Wireless Charger Black",
                        "variantSellPrice": "5.10",
                    }
                ]

            def get_variant_stock(self, variant_id):
                return 250

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": "Test Free Shipping",
                        "logisticPrice": "0.00",
                        "logisticAging": "7-12",
                    },
                ]

        class FakeExchangeRateClient:

            def get_rate(
                self,
                from_currency,
                to_currency,
            ):
                self.from_currency = from_currency
                self.to_currency = to_currency

                return Decimal("0.86")

        cj_client = FakeCJClient()
        exchange_rate_client = FakeExchangeRateClient()

        pipeline = CJPipelineService(
            client=cj_client,
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=CurrencyConversionService(),
            exchange_rate_client=exchange_rate_client,
        )

        bridge = EtsyCJBridgeService(
            cj_pipeline_service=pipeline,
            cj_client=cj_client,
        )

        opportunity = bridge.search_and_create_opportunity(
            market_observation=observation,
            supplier=supplier,
        )

        offer = supplier.offers.get()

        self.assertEqual(
            offer.market_observation,
            observation,
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("4.39"),
        )

        self.assertEqual(
            offer.currency,
            "EUR",
        )

        self.assertEqual(
            offer.stock,
            250,
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("4.39"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.name,
            "Wireless Charger",
        )

        self.assertEqual(
            exchange_rate_client.from_currency,
            "USD",
        )

        self.assertEqual(
            exchange_rate_client.to_currency,
            "EUR",
        )

