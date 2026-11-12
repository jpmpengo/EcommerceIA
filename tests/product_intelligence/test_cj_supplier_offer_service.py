from decimal import Decimal

from django.test import TestCase

from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)

from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)

from product_intelligence.models import (
    MarketObservation,
    ProductIdea,
    Supplier,
    SupplierOffer,
)

class CJSupplierOfferServiceTests(TestCase):

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        self.service = CJSupplierOfferService()

    def test_creates_supplier_offer(self):
        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "image_url": "https://example.com/image.jpg",
            "purchase_price": "8.75",
            "product_url": "https://example.com/cj-product",
            "stock": 42,
            "stock_country": "FR",
            "shipping_cost": "3.20",
        }

        product["product_description"] = "USB-C 20W, compatible Qi, protection thermique"

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertEqual(
            offer.supplier,
            self.supplier,
        )

        self.assertEqual(
            offer.product_name,
            "Wireless Charger",
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("8.75"),
        )

        self.assertEqual(
            offer.shipping_cost,
            Decimal("3.20"),
        )

        self.assertEqual(
            offer.stock,
            42,
        )

        self.assertEqual(
            offer.stock_country,
            "FR",
        )

        self.assertEqual(
            offer.stock_country,
            "FR",
        )

        offer.refresh_from_db()
        self.assertEqual(offer.product_description, product["product_description"])

    def test_create_offer_persists_explicit_free_shipping(self):
        product = {
            "external_id": "CJ-FREE-001",
            "name": "Supplier Shipped Product",
            "purchase_price": "8.75",
            "free_shipping": True,
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertIs(offer.free_shipping, True)

    def test_keeps_shipping_cost_unknown_when_missing(self):
        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "purchase_price": "8.75",
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertIsNone(
            offer.shipping_cost
        )


    def test_accepts_product_without_stock(self):
        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "purchase_price": "8.75",
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertIsNone(
            offer.stock,
        )

    def test_creates_supplier_offer_with_currency(self):
        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "purchase_price": "8.75",
            "currency": "USD",
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertEqual(
            offer.currency,
            "USD",
        )

    def test_uses_default_currency_when_currency_missing(self):
        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "purchase_price": "8.75",
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertEqual(
            offer.currency,
            "EUR",
        )

    def test_uses_default_currency_when_cj_currency_is_none(self):
        product = {
            "external_id": "CJ-123",
            "name": "Wireless Charger",
            "purchase_price": "5.10",
            "currency": None,
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertEqual(
            offer.currency,
            "EUR",
        )

    def test_creates_offer_from_cj_variant_price_and_stock(self):
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

        stock = 14759

        offer = self.service.create_offer_from_variant(
            supplier=self.supplier,
            product=product,
            variant=variant,
            stock=stock,
        )

        self.assertEqual(
            offer.supplier,
            self.supplier,
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

    def test_create_offer_keeps_supplier_product_id(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-PRODUCT-123",
            "name": "Wireless Charger",
            "purchase_price": "4.53",
            "currency": "EUR",
            "stock": 250,
        }

        service = CJSupplierOfferService()

        offer = service.create_offer(
            supplier=supplier,
            product=product,
        )

        self.assertEqual(
            offer.supplier_product_id,
            "CJ-PRODUCT-123",
        )

    def test_create_offer_keeps_supplier_image_url(self):
        product = {
            "external_id": "CJ-IMAGE-001",
            "name": "Wireless Charger",
            "purchase_price": "4.53",
            "currency": "EUR",
            "stock": 250,
            "image_url": (
                "https://example.com/"
                "wireless-charger.jpg"
            ),
        }

        offer = self.service.create_offer(
            supplier=self.supplier,
            product=product,
        )

        self.assertEqual(
            offer.image_url,
            (
                "https://example.com/"
                "wireless-charger.jpg"
            ),
        )

    def test_create_offer_from_variant_keeps_supplier_image_url(self):
        product = {
            "external_id": "CJ-IMAGE-002",
            "name": "Wireless Charger",
            "currency": "USD",
            "image_url": (
                "https://example.com/"
                "wireless-charger-variant.jpg"
            ),
        }

        variant = {
            "pid": "CJ-IMAGE-002",
            "variantNameEn": "Wireless Charger Black",
            "variantSellPrice": "5.25",
        }

        offer = self.service.create_offer_from_variant(
            supplier=self.supplier,
            product=product,
            variant=variant,
            stock=100,
        )

        self.assertEqual(
            offer.image_url,
            (
                "https://example.com/"
                "wireless-charger-variant.jpg"
            ),
        )

    def test_create_offer_from_variant_keeps_variant_id(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-PRODUCT-123",
            "name": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "vid": "CJ-VARIANT-456",
            "pid": "CJ-PRODUCT-123",
            "variantNameEn": (
                "Gaming Mouse Pad Black 80x40x2cm"
            ),
            "variantSellPrice": "7.33",
        }

        service = CJSupplierOfferService()

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=100,
        )

        self.assertEqual(
            offer.supplier_product_id,
            "CJ-VARIANT-456",
        )

    def test_create_offer_from_variant_persists_free_shipping(self):
        product = {
            "external_id": "CJ-FREE-002",
            "name": "Supplier shipped product",
            "currency": "USD",
            "free_shipping": True,
        }
        variant = {
            "vid": "CJ-FREE-VARIANT-002",
            "pid": "CJ-FREE-002",
            "variantNameEn": "Supplier shipped product",
            "variantSellPrice": "7.50",
        }

        offer = self.service.create_offer_from_variant(
            supplier=self.supplier,
            product=product,
            variant=variant,
            stock=100,
        )

        self.assertIs(offer.free_shipping, True)

    def test_create_offer_from_variant_persists_supplier_identity_and_weight(self):
        product = {
            "external_id": "CJ-PARENT-001",
            "name": "Supplier shipped product",
            "currency": "USD",
        }
        variant = {
            "vid": "CJ-VARIANT-001",
            "pid": "CJ-PARENT-001",
            "variantSku": "CJ-SKU-001",
            "variantNameEn": "Supplier shipped product",
            "variantSellPrice": "7.50",
            "variantWeight": 320,
        }

        offer = self.service.create_offer_from_variant(
            supplier=self.supplier,
            product=product,
            variant=variant,
            stock=100,
        )

        self.assertEqual(offer.supplier_parent_product_id, "CJ-PARENT-001")
        self.assertEqual(offer.supplier_sku, "CJ-SKU-001")
        self.assertEqual(offer.shipping_weight_grams, 320)

    def test_create_offer_from_variant_converts_float_price_cleanly(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-PRODUCT-123",
            "name": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "vid": "CJ-VARIANT-456",
            "pid": "CJ-PRODUCT-123",
            "variantNameEn": (
                "Gaming Mouse Pad Black 80x40x2cm"
            ),
            "variantSellPrice": 7.33,
        }

        service = CJSupplierOfferService()

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=40000,
        )

        self.assertEqual(
            offer.purchase_price,
            Decimal("7.33"),
        )

    def test_create_offer_from_variant_stores_variant_features(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        product = {
            "external_id": "CJ-PRODUCT-123",
            "name": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "vid": "CJ-VARIANT-456",
            "pid": "CJ-PRODUCT-123",
            "variantNameEn": (
                "Competitive Gaming Office "
                "Waterproof Mouse Pad "
                "Black 80x40x2cm"
            ),
            "variantSellPrice": 7.33,
        }

        service = CJSupplierOfferService(
            variant_features_service=(
                VariantFeaturesService()
            ),
        )

        offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=40000,
        )

        self.assertEqual(
            offer.variant_features,
            {
                "dimensions_mm": [
                    800,
                    400,
                ],
                "color": "Black",
            },
        )

    def test_variant_features_extracts_apparel_size(self):
        features = VariantFeaturesService().extract(
            {
                "variantNameEn": (
                    "Women's Physiological Underwear Black 2XL"
                ),
            }
        )

        self.assertEqual(features["color"], "Black")
        self.assertEqual(features["size"], "2XL")

    def test_create_offer_from_variant_updates_existing_offer(
        self,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )

        service = CJSupplierOfferService(
            variant_features_service=(
                VariantFeaturesService()
            ),
        )

        product = {
            "external_id": "P1",
            "name": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "vid": "V1",
            "pid": "P1",
            "variantNameEn": (
                "Gaming Mouse Pad Black 80x40cm"
            ),
            "variantSellPrice": "7.33",
        }

        first_offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=100,
        )

        variant["variantSellPrice"] = "6.99"

        second_offer = service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=250,
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
            Decimal("6.99"),
        )

        self.assertEqual(
            second_offer.stock,
            250,
        )

    def test_keeps_separate_variant_offer_per_market_observation(
        self,
    ):
        first_observation = (
            MarketObservation.objects.create(
                source="etsy",
                external_id="WC-A",
                name="Gaming Mouse Pad",
                observed_price=Decimal("49.90"),
                currency="EUR",
                product_url="http://localhost/wc-a",
            )
        )

        second_observation = (
            MarketObservation.objects.create(
                source="etsy",
                external_id="ETSY-A1",
                name="Gaming Mouse Pad",
                observed_price=Decimal("51.96"),
                currency="EUR",
                product_url="https://etsy.com/a1",
            )
        )

        product = {
            "external_id": "CJ-PRODUCT-123",
            "name": "Gaming Mouse Pad",
            "currency": "USD",
        }

        variant = {
            "vid": "CJ-VARIANT-456",
            "variantNameEn": (
                "Gaming Mouse Pad 90x40"
            ),
            "variantSellPrice": "7.33",
        }

        first_offer = (
            self.service.create_offer_from_variant(
                supplier=self.supplier,
                product=product,
                variant=variant,
                stock=100,
                market_observation=(
                    first_observation
                ),
            )
        )

        second_offer = (
            self.service.create_offer_from_variant(
                supplier=self.supplier,
                product=product,
                variant=variant,
                stock=100,
                market_observation=(
                    second_observation
                ),
            )
        )

        self.assertNotEqual(
            first_offer.id,
            second_offer.id,
        )

        self.assertEqual(
            first_offer.market_observation,
            first_observation,
        )
        self.assertEqual(
            second_offer.market_observation,
            second_observation,
        )

        self.assertEqual(
            SupplierOffer.objects.count(),
            2,
        )

    def test_create_offer_from_variant_links_product_idea(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Tapis de bureau ergonomiques",
            customer_problem=(
                "Améliorer le confort du bureau."
            ),
            target_customer=(
                "Télétravailleurs européens."
            ),
            reason_to_study=(
                "Catégorie soutenue par "
                "des signaux publics."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "tapis bureau ergonomique",
            ],
            demand_signals=[
                "Intérêt public documenté.",
            ],
            evidence_sources=[
                {
                    "title": "Source publique",
                    "url": (
                        "https://example.com/source"
                    ),
                    "evidence": (
                        "La source décrit la demande."
                    ),
                },
            ],
            status="selected",
        )

        product = {
            "external_id": "CJ-PRODUCT-IDEA",
            "name": "Ergonomic Desk Mat",
            "currency": "USD",
        }

        variant = {
            "vid": "CJ-VARIANT-IDEA",
            "variantNameEn": (
                "Ergonomic Desk Mat 90x40"
            ),
            "variantSellPrice": "7.33",
        }

        offer = (
            self.service
            .create_offer_from_variant(
                supplier=self.supplier,
                product=product,
                variant=variant,
                stock=100,
                product_idea=idea,
            )
        )

        self.assertEqual(
            offer.product_idea,
            idea,
        )

        self.assertIsNone(
            offer.market_observation,
        )

    

    def test_create_offer_from_variant_stores_supplier_search_keyword(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )
        product = {
            "external_id": "CJ-PRODUCT-KEYWORD",
            "name": "Bike Light",
            "currency": "USD",
        }
        variant = {
            "vid": "CJ-VARIANT-KEYWORD",
            "pid": "CJ-PRODUCT-KEYWORD",
            "variantNameEn": "USB Rechargeable Bike Light",
            "variantSellPrice": "8.50",
        }
        offer = CJSupplierOfferService().create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=100,
            supplier_search_keyword="USB rechargeable bike light",
        )
        self.assertEqual(
            offer.supplier_search_keyword,
            "USB rechargeable bike light",
        )
