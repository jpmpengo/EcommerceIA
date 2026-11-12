from decimal import Decimal

from django.test import TestCase

from dashboard.services.commercial_name_suggestion_service import (
    CommercialNameSuggestionService,
)
from product_intelligence.models import ProductOpportunity


class CommercialNameSuggestionServiceTests(TestCase):

    def test_suggests_commercial_name_for_makeup_storage_box(self):
        opportunity = ProductOpportunity.objects.create(
            name=(
                "Makeup Storage Box With LED Light Mirror Portable Travel "
                "Makeup Cosmetics Storage Box Touch Light Storage Organizer "
                "Cherry Blossom Pink USB"
            ),
            source_name="CJdropshipping",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
        )

        suggestion = CommercialNameSuggestionService.suggest(opportunity)

        self.assertLess(len(suggestion), len(opportunity.name))
        self.assertIn("rangement", suggestion.lower())
        self.assertIn("maquillage", suggestion.lower())
        self.assertIn("led", suggestion.lower())

    def test_uses_product_idea_context_for_under_sink_organizer(self):
        from product_intelligence.models import ProductIdea, Supplier, SupplierOffer

        idea = ProductIdea.objects.create(
            name="Organisateurs modulaires pour petits espaces de cuisine : tiroirs, placards et sous-évier",
            customer_problem="Manque d’espace et difficulté à organiser les produits de nettoyage dans les cuisines compactes.",
            target_customer="Locataires et propriétaires vivant en appartement.",
        )
        supplier = Supplier.objects.create(name="CJ Test Commercial Name")
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_idea=idea,
            product_name="Desktop Storage Box With Wheels Under Sink Organizer For Miscellaneous Items Creamy Yellow Small Short With Wheels 1pc",
            purchase_price=Decimal("10.00"),
        )
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name="CJdropshipping",
            supplier_offer=offer,
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
        )

        suggestion = CommercialNameSuggestionService.suggest(opportunity)

        self.assertLess(len(suggestion), len(opportunity.name))
        self.assertIn("sous-évier", suggestion.lower())
        self.assertIn("roulettes", suggestion.lower())

    def test_shortens_long_supplier_name(self):
        opportunity = ProductOpportunity.objects.create(
            name=(
                "F3 light USB bicycle headlights 3 t6 mountain bike "
                "rechargeable light LED lights professional riding bike lights Black"
            ),
            source_name="CJdropshipping",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
        )

        suggestion = CommercialNameSuggestionService.suggest(opportunity)

        self.assertIsNotNone(suggestion)
        self.assertLess(len(suggestion), len(opportunity.name))
        self.assertIn("vélo", suggestion.lower())
        self.assertIn("rechargeable", suggestion.lower())
