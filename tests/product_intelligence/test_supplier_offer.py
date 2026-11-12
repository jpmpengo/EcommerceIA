from decimal import Decimal

from django.test import TestCase

from django.utils import timezone

from product_intelligence.models import (
    MarketObservation,
    Supplier,
    SupplierOffer,
)

from product_intelligence.models import (
    MarketObservation,
    ProductIdea,
    Supplier,
    SupplierOffer,
)

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

    def test_supplier_offer_stores_shipping_weight_grams(
        self,
    ):
        supplier = Supplier.objects.create(
            name="Test Supplier Weight",
            country="FR",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Macrame Pot Holder",
            purchase_price=Decimal("10.96"),
            shipping_cost=None,
            currency="EUR",
            shipping_weight_grams=230,
        )

        offer.refresh_from_db()

        self.assertEqual(
            offer.shipping_weight_grams,
            230,
        )

    def test_supplier_offer_can_be_linked_to_product_idea(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Accessoires de bureau ergonomiques",
            customer_problem=(
                "Améliorer le confort de travail."
            ),
            target_customer=(
                "Télétravailleurs européens."
            ),
            reason_to_study=(
                "Des signaux publics indiquent "
                "un intérêt pour cette catégorie."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "accessoire bureau ergonomique",
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

        supplier = Supplier.objects.create(
            name="Fournisseur Test",
            country="FR",
            website="https://example.com",
            supplier_type="wholesaler",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_idea=idea,
            product_name=(
                "Support ergonomique réglable"
            ),
            purchase_price=Decimal("12.00"),
            currency="EUR",
            stock=50,
        )

        self.assertEqual(
            offer.product_idea,
            idea,
        )

        self.assertIn(
            offer,
            idea.supplier_offers.all(),
        )



    def test_persists_visual_matching_result(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            supplier_type="dropshipper",
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="USB Bike Light",
            purchase_price="8.50",
            currency="USD",
            visual_match_classification="rejected",
            visual_score=28,
            same_product_probability=5,
            visual_match_evidence="Phare avant seul.",
            visual_match_differences=[
                "Absence de feu arriere",
            ],
        )

        offer.refresh_from_db()

        self.assertEqual(
            offer.visual_match_classification,
            "rejected",
        )
        self.assertEqual(offer.visual_score, 28)
        self.assertEqual(
            offer.same_product_probability,
            5,
        )
        self.assertEqual(
            offer.visual_match_evidence,
            "Phare avant seul.",
        )
        self.assertEqual(
            offer.visual_match_differences,
            ["Absence de feu arriere"],
        )
