from django.test import TestCase

from product_intelligence.services.cj_pipeline import (
    CJPipelineService,
)

from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)

from decimal import Decimal

from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)

from product_intelligence.models import (
    MarketObservation,
    Supplier,
)

from product_intelligence.services.cj_pipeline import CJPipelineService

from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)

class FakeCJClient:

    def get_product_detail(self, product_id):
        return {
            "id": product_id,
            "nameEn": "Wireless Charger",
            "bigImage": "https://example.com/image.jpg",
            "sellPrice": "8.75",
        }

    def get_product_variants(self, product_id):
        return [
            {
                "vid": "VARIANT-123",
                "pid": product_id,
                "variantNameEn": "Black",
                "variantSellPrice": "9.25",
            }
        ]

    def get_variant_stock(self, variant_id):
        return 42

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

    def normalize_product(self, product):
        return {
            "external_id": product["id"],
            "name": product["nameEn"],
            "image_url": product["bigImage"],
            "purchase_price": product["sellPrice"],
            "currency": "USD",
        }


class CJPipelineServiceTests(TestCase):

    def test_builds_supplier_product_from_cj_data(self):
        service = CJPipelineService(
            client=FakeCJClient(),
        )

        product = service.build_supplier_product(
            product_id="CJ-123",
        )

        self.assertEqual(
            product["external_id"],
            "CJ-123",
        )

        self.assertEqual(
            product["name"],
            "Wireless Charger",
        )

        self.assertEqual(
            product["purchase_price"],
            "9.25",
        )

        self.assertEqual(
            product["stock"],
            42,
        )

    def test_uses_variant_price_when_variant_exists(self):
        service = CJPipelineService(
            client=FakeCJClient(),
        )

        product = service.build_supplier_product(
            product_id="CJ-123",
        )

        self.assertEqual(
            product["purchase_price"],
            "9.25",
        )

    def test_builds_supplier_offer_from_cj_product(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
        )

        offer = service.build_supplier_offer(
            supplier=supplier,
            product_id="CJ-123",
        )

        self.assertEqual(
            offer.supplier,
            supplier,
        )

        self.assertEqual(
            offer.product_name,
            "Wireless Charger",
        )   

        self.assertEqual(
            str(offer.purchase_price),
            "9.25",
        )

        self.assertEqual(
            offer.stock,
            42,
        )

    def test_builds_product_opportunity_from_cj_product(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
        )

        opportunity = service.build_product_opportunity(
            supplier=supplier,
            product_id="CJ-123",
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.name,
            "Wireless Charger",
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("9.25"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.source_name,
            "CJdropshipping",
        )

    def test_builds_supplier_offer_linked_to_market_observation(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-123",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
        )

        offer = service.build_supplier_offer(
            supplier=supplier,
            product_id="CJ-123",
            market_observation=observation,
        )

        self.assertEqual(
            offer.market_observation,
            observation,
        )

    def test_builds_opportunity_from_market_observation(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-456",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=(
                CurrencyConversionService()
            ),
            exchange_rate=Decimal("1.00"),
        )

        opportunity = service.build_opportunity_from_observation(
            supplier=supplier,
            product_id="CJ-123",
            market_observation=observation,
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("9.25"),
        )

        self.assertEqual(
            opportunity.source_name,
            "CJdropshipping",
        )

        offer = supplier.offers.get()

        self.assertEqual(
            offer.market_observation,
            observation,
        )

    def test_refuses_opportunity_without_market_price(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-NO-PRICE",
            name="Wireless Charger",
            observed_price=None,
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
        )

        with self.assertRaises(ValueError):
            service.build_opportunity_from_observation(
                supplier=supplier,
                product_id="CJ-123",
                market_observation=observation,
            )

    def test_builds_supplier_product_when_no_variant_exists(self):
        class CJClientWithoutVariants(FakeCJClient):

            def get_product_variants(self, product_id):
                return []

        service = CJPipelineService(
            client=CJClientWithoutVariants(),
        )

        product = service.build_supplier_product(
            product_id="CJ-123",
        )

        self.assertEqual(
            product["external_id"],
            "CJ-123",
        )

        self.assertEqual(
            product["purchase_price"],
            "8.75",
        )

        self.assertNotIn(
            "stock",
            product,
        )

    def test_keeps_product_price_when_variant_has_no_price(self):
        class CJClientWithVariantWithoutPrice(FakeCJClient):

            def get_product_variants(self, product_id):
                return [
                    {
                        "vid": "VARIANT-123",
                        "pid": product_id,
                        "variantNameEn": "Black",
                    }
                ]

        service = CJPipelineService(
            client=CJClientWithVariantWithoutPrice(),
        )

        product = service.build_supplier_product(
            product_id="CJ-123",
        )

        self.assertEqual(
            product["purchase_price"],
            "8.75",
        )

        self.assertEqual(
            product["stock"],
            42,
        )

    def test_builds_supplier_product_with_unknown_stock(self):
        class CJClientWithoutStock(FakeCJClient):

            def get_variant_stock(self, variant_id):
                return None

        service = CJPipelineService(
            client=CJClientWithoutStock(),
        )

        product = service.build_supplier_product(
            product_id="CJ-123",
        )

        self.assertEqual(
            product["purchase_price"],
            "9.25",
        )

        self.assertIsNone(
            product["stock"],
        )

    def test_refuses_opportunity_when_currencies_are_different(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-USD-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        class CJClientInUSD(FakeCJClient):

            def normalize_product(self, product):
                normalized = super().normalize_product(product)
                normalized["currency"] = "USD"
                return normalized

        service = CJPipelineService(
            client=CJClientInUSD(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "Supplier and market currencies must match.",
        ):
            service.build_opportunity_from_observation(
                supplier=supplier,
                product_id="CJ-123",
                market_observation=observation,
            )
        
    def test_builds_supplier_offer_from_cj_variant(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-123",
            "name": "Three in one wireless charger",
            "currency": "USD",
        }

        variant = {
            "vid": "1795624342437502976",
            "variantSku": "CJXFLPCD00284-Rose Gold",
            "variantNameEn": (
                "Three in one wireless charger Rose Gold"
            ),
            "variantSellPrice": "7.30",
            "variantWeight": 300.0,
        }

        class FakeVariantCJClient:
            def get_product_detail(self, product_id):
                return {
                    "pid": product_id,
                    "productNameEn": product["name"],
                    "variants": [variant],
                }

            def get_variant_stock(self, variant_id):
                self.requested_variant_id = variant_id
                return 14759

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "Test Free Shipping"
                        ),
                        "logisticPrice": "0.00",
                        "logisticAging": "7-12",
                    },
                ]

        client = FakeVariantCJClient()

        service = CJPipelineService(
            client=client,
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
        )

        offer = service.build_supplier_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        self.assertEqual(
            offer.product_name,
            "Three in one wireless charger Rose Gold",
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("7.30"),
        )

        self.assertEqual(
            offer.stock,
            14759,
        )

        self.assertEqual(
            offer.currency,
            "USD",
        )

        self.assertEqual(
            client.requested_variant_id,
            "1795624342437502976",
        )

    def test_builds_opportunity_from_market_observation_and_variant(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-VARIANT-001",
            name="Three in one wireless charger",
            observed_price=Decimal("19.90"),
            currency="USD",
            product_url="https://example.com/ebay-product",
        )

        product = {
            "external_id": "CJ-123",
            "name": "Three in one wireless charger",
            "currency": "USD",
        }

        variant = {
            "vid": "1795624342437502976",
            "variantSku": "CJXFLPCD00284-Rose Gold",
            "variantNameEn": (
                "Three in one wireless charger Rose Gold"
            ),
            "variantSellPrice": "7.30",
            "variantWeight": 300.0,
        }

        class FakeVariantCJClient:
            def get_variant_stock(self, variant_id):
                return 14759

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "Test Free Shipping"
                        ),
                        "logisticPrice": "0.00",
                        "logisticAging": "7-12",
                    },
                ]

        service = CJPipelineService(
            client=FakeVariantCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
        )

        opportunity = service.build_opportunity_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            market_observation=observation,
        )

        self.assertEqual(
            opportunity.name,
            "Three in one wireless charger Rose Gold",
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("7.30"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.source_name,
            "CJdropshipping",
        )

        offer = supplier.offers.get()

        self.assertEqual(
            offer.market_observation,
            observation,
        )

        self.assertEqual(
            offer.stock,
            14759,
        )

    def test_converts_variant_price_to_market_currency(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-EUR-001",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "currency": "USD",
        }

        variant = {
            "vid": "VARIANT-123",
            "variantSku": "CJ-TEST-123",
            "variantNameEn": "Wireless Charger Black",
            "variantSellPrice": "7.30",
        }

        class FakeCJClient:
            def get_variant_stock(self, variant_id):
                return 100

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "Test Free Shipping"
                        ),
                        "logisticPrice": "0.00",
                        "logisticAging": "7-12",
                    },
                ]

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=CurrencyConversionService(),
            exchange_rate=Decimal("0.86"),
        )

        opportunity = service.build_opportunity_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            market_observation=observation,
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("6.28"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

    def test_uses_exchange_rate_client_for_currency_conversion(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-EUR-002",
            name="Wireless Charger",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "currency": "USD",
        }

        variant = {
            "vid": "VARIANT-123",
            "variantSku": "CJ-TEST-123",
            "variantNameEn": "Wireless Charger Black",
            "variantSellPrice": "7.30",
        }

        class FakeCJClient:
            def get_variant_stock(self, variant_id):
                return 100

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "Test Free Shipping"
                        ),
                        "logisticPrice": "0.00",
                        "logisticAging": "7-12",
                    },
                ]

        class FakeExchangeRateClient:
            def get_rate(self, from_currency, to_currency):
                self.from_currency = from_currency
                self.to_currency = to_currency
                return Decimal("0.86")

        exchange_rate_client = FakeExchangeRateClient()

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=CurrencyConversionService(),
            exchange_rate_client=exchange_rate_client,
        )

        opportunity = service.build_opportunity_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            market_observation=observation,
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("6.28"),
        )

        self.assertEqual(
            exchange_rate_client.from_currency,
            "USD",
        )

        self.assertEqual(
            exchange_rate_client.to_currency,
            "EUR",
        )

    def test_creates_converted_offer_and_opportunity_from_variant(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="EBAY-END-TO-END-001",
            name="Wireless Controller Charger",
            observed_price=Decimal("14.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        product = {
            "external_id": "CJ-REAL-LIKE-001",
            "name": "Wireless controller charger",
            "currency": "USD",
        }

        variant = {
            "vid": "VARIANT-REAL-LIKE-001",
            "variantSku": "CJXFSPYX00413-Black-USB",
            "variantNameEn": (
                "Wireless controller charger Black USB"
            ),
            "variantSellPrice": "5.10",
            "variantWeight": 250.0,
        }

        class FakeCJClient:
            def get_variant_stock(self, variant_id):
                self.variant_id = variant_id
                return 20000

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "Test Free Shipping"
                        ),
                        "logisticPrice": "0.00",
                        "logisticAging": "7-12",
                    },
                ]

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "Test Free Shipping"
                        ),
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

                return Decimal("0.865948")

        cj_client = FakeCJClient()
        exchange_rate_client = FakeExchangeRateClient()

        service = CJPipelineService(
            client=cj_client,
            offer_service=CJSupplierOfferService(),
            opportunity_service=SupplierOfferOpportunityService(),
            currency_conversion_service=CurrencyConversionService(),
            exchange_rate_client=exchange_rate_client,
        )

        opportunity = service.build_opportunity_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            market_observation=observation,
        )

        offer = supplier.offers.get()

        # Prix CJ :
        # 5.10 USD * 0.865948 = 4.4163348
        # => 4.42 EUR

        self.assertEqual(
            offer.purchase_price,
            Decimal("4.42"),
        )

        self.assertEqual(
            offer.currency,
            "EUR",
        )

        self.assertEqual(
            offer.stock,
            20000,
        )

        self.assertEqual(
            offer.market_observation,
            observation,
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("4.42"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("14.90"),
        )

        self.assertEqual(
            cj_client.variant_id,
            "VARIANT-REAL-LIKE-001",
        )

        self.assertEqual(
            exchange_rate_client.from_currency,
            "USD",
        )

        self.assertEqual(
            exchange_rate_client.to_currency,
            "EUR",
        )

    def test_build_supplier_product_uses_variant_price_when_product_price_is_range(
        self,
    ):
        class CJClientWithPriceRange(FakeCJClient):

            def get_product_detail(
                self,
                product_id,
            ):
                return {
                    "id": product_id,
                    "nameEn": "Wireless Charger",
                    "bigImage": "https://example.com/image.jpg",
                    "sellPrice": "2.87 -- 7.23",
                }

            def normalize_product(
                self,
                product,
            ):
                return {
                    "external_id": product["id"],
                    "name": product["nameEn"],
                    "image_url": product["bigImage"],
                    "purchase_price": product["sellPrice"],
                    "currency": "USD",
                }

            def get_product_variants(
                self,
                product_id,
            ):
                return [
                    {
                        "vid": "VARIANT-123",
                        "pid": product_id,
                        "variantNameEn": "Black",
                        "variantSellPrice": "4.53",
                    }
                ]

            def get_variant_stock(
                self,
                variant_id,
            ):
                return 100

        service = CJPipelineService(
            client=CJClientWithPriceRange(),
        )

        product = service.build_supplier_product(
            product_id="CJ-123",
        )

        self.assertEqual(
            product["purchase_price"],
            "4.53",
        )

        self.assertEqual(
            product["stock"],
            100,
        )

    def test_refuses_price_range_when_no_variant_exists(
        self,
    ):
        class CJClientWithPriceRangeWithoutVariants(
            FakeCJClient
        ):

            def get_product_detail(
                self,
                product_id,
            ):
                return {
                    "id": product_id,
                    "nameEn": "Wireless Charger",
                    "bigImage": "https://example.com/image.jpg",
                    "sellPrice": "2.87 -- 7.23",
                }

            def normalize_product(
                self,
                product,
            ):
                return {
                    "external_id": product["id"],
                    "name": product["nameEn"],
                    "image_url": product["bigImage"],
                    "purchase_price": product["sellPrice"],
                    "currency": "USD",
                }

            def get_product_variants(
                self,
                product_id,
            ):
                return []

        service = CJPipelineService(
            client=CJClientWithPriceRangeWithoutVariants(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "CJ product price must be a single numeric value.",
        ):
            service.build_supplier_product(
                product_id="CJ-123",
            )   

    def test_converts_shipping_cost_to_market_currency(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        observation = MarketObservation.objects.create(
            source="etsy",
            external_id="ETSY-SHIPPING-1",
            name="Wireless Charger",
            observed_price=Decimal("29.90"),
            currency="EUR",
            product_url="https://example.com/product",
        )

        class FakeCJClient:

            def get_variant_stock(
                self,
                variant_id,
            ):
                return 42

            def calculate_freight(
                self,
                variant_id,
                origin_country,
                destination_country,
                quantity=1,
            ):
                return [
                    {
                        "logisticName": (
                            "CJ Standard"
                        ),
                        "logisticPrice": "5.00",
                        "logisticAging": "7-12",
                    },
                ]

        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "currency": "USD",
            "image_url": "",
        }

        variant = {
            "vid": "VARIANT-123",
            "pid": "CJ-123",
            "variantNameEn": (
                "Wireless Charger Black"
            ),
            "variantSellPrice": "10.00",
        }

        service = CJPipelineService(
            client=FakeCJClient(),
            offer_service=(
                CJSupplierOfferService()
            ),
            opportunity_service=(
                SupplierOfferOpportunityService()
            ),
            currency_conversion_service=(
                CurrencyConversionService()
            ),
            exchange_rate=Decimal("0.90"),
        )

        opportunity = (
            service.build_opportunity_from_variant(
                supplier=supplier,
                product=product,
                variant=variant,
                market_observation=observation,
            )
        )

        self.assertIsNotNone(
            opportunity
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("9.00"),
        )

        self.assertEqual(
            opportunity.shipping_cost,
            Decimal("4.50"),
        )

        self.assertEqual(
            opportunity.get_total_cost(),
            Decimal("13.50"),
        )

        offer = opportunity.supplier_offer

        self.assertEqual(
            offer.currency,
            "EUR",
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("9.00"),
        )

        self.assertEqual(
            offer.shipping_cost,
            Decimal("4.50"),
        )

    

    