from decimal import Decimal

from django.test import TestCase

from django.utils import timezone

from product_intelligence.models import (
    MarketObservation,
    Supplier,
    SupplierOffer,
)

from decimal import Decimal

class SupplierOfferTests(TestCase):

    def test_supplier_offer_can_be_created(self):
        supplier = Supplier.objects.create(
            name="Fournisseur Test",
            country="FR",
            website="https://example.com",
            supplier_type="wholesaler",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Produit Test",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("2.50"),
            currency="EUR",
            stock=100,
            product_url="https://example.com/product",
        )

        self.assertEqual(offer.supplier, supplier)
        self.assertEqual(offer.product_name, "Produit Test")
        self.assertEqual(offer.purchase_price, Decimal("10.00"))
        self.assertEqual(offer.shipping_cost, Decimal("2.50"))
        self.assertEqual(offer.currency, "EUR")
        self.assertEqual(offer.stock, 100)

    def test_supplier_offer_can_be_linked_to_market_observation(self):
        supplier = Supplier.objects.create(
            name="Fournisseur Test",
            country="FR",
            website="https://example.com",
            supplier_type="wholesaler",
        )

        observation = MarketObservation.objects.create(
            source="ebay",
            external_id="ebay-123",
            name="Produit eBay Test",
            observed_price=Decimal("19.90"),
            currency="EUR",
            product_url="https://example.com/ebay-product",
        )

        observed_at = timezone.now()

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            market_observation=observation,
            product_name="Produit Test",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("2.50"),
            currency="EUR",
            stock=100,
            product_url="https://example.com/product",
            observed_at=observed_at,
        )

        self.assertEqual(
            offer.market_observation,
            observation,
        )

        self.assertEqual(
            offer.observed_at,
            observed_at,
        )

    def test_supplier_offer_stores_variant_features(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Test Supplier",
            country="FR",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Gaming Mouse Pad",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            variant_features={
                "dimensions_mm": [
                    800,
                    400,
                ],
                "color": "Black",
            },
        )

        offer.refresh_from_db()

        self.assertEqual(
            offer.variant_features[
                "dimensions_mm"
            ],
            [800, 400],
        )

        self.assertEqual(
            offer.variant_features[
                "color"
            ],
            "Black",
        )


