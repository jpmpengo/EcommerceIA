from decimal import Decimal

from django.test import TestCase

from dashboard.services.description_suggestion_service import (
    DescriptionSuggestionService,
)
from product_intelligence.models import ProductOpportunity


class DescriptionSuggestionServiceTests(TestCase):

    def test_suggests_description_for_opportunity(self):
        opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth ANC",
            source_name="Test",
            supplier_price=Decimal("30.00"),
            market_price=Decimal("79.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("2.00"),
            demand_score=85,
            competition_score=35,
            status="approved",
            description="Bon produit.",
            initial_stock=5,
        )

        suggestion = DescriptionSuggestionService.suggest(
            opportunity
        )

        self.assertIsNotNone(
            suggestion
        )

        self.assertGreaterEqual(
            len(suggestion),
            50,
        )

        self.assertIn(
            opportunity.name,
            suggestion,
        )
  
    def test_uses_product_idea_context_for_customer_description(self):
        from product_intelligence.models import ProductIdea, Supplier, SupplierOffer

        idea = ProductIdea.objects.create(
            name="Accessoires ergonomiques compacts pour télétravail",
            customer_problem="Réduire l’inconfort lié à une mauvaise posture devant un ordinateur portable.",
            target_customer="Télétravailleurs et étudiants utilisant un ordinateur portable plusieurs heures par jour.",
            reason_to_study="Besoin ergonomique documenté.",
            countries=["FR"],
        )
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_idea=idea,
            product_name="Portable Laptop Stand Adjustable Foldable Aluminum Holder Silver",
            purchase_price=Decimal("10.00"),
        )
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=supplier.name,
            supplier_price=Decimal("10.00"),
            market_price=Decimal("35.00"),
            supplier_offer=offer,
        )

        suggestion = DescriptionSuggestionService.suggest(opportunity)

        self.assertIn("mauvaise posture", suggestion.lower())
        self.assertIn("télétravailleurs", suggestion.lower())

    def test_uses_product_idea_context_for_customer_description(self):
        from product_intelligence.models import ProductIdea, Supplier, SupplierOffer

        idea = ProductIdea.objects.create(
            name="Accessoires ergonomiques compacts pour télétravail",
            customer_problem="Réduire l’inconfort lié à une mauvaise posture devant un ordinateur portable.",
            target_customer="Télétravailleurs et étudiants utilisant un ordinateur portable plusieurs heures par jour.",
            reason_to_study="Besoin ergonomique documenté.",
            countries=["FR"],
        )
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_idea=idea,
            product_name="Portable Laptop Stand Adjustable Foldable Aluminum Holder Silver",
            purchase_price=Decimal("10.00"),
        )
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=supplier.name,
            supplier_price=Decimal("10.00"),
            market_price=Decimal("35.00"),
            supplier_offer=offer,
        )

        suggestion = DescriptionSuggestionService.suggest(opportunity)

        self.assertIn("mauvaise posture", suggestion.lower())
        self.assertIn("télétravailleurs", suggestion.lower())

    def test_does_not_expose_internal_financial_analysis(self):
        opportunity = ProductOpportunity.objects.create(
            name="Boîte de rangement avec miroir LED",
            source_name="CJdropshipping",
            supplier_price=Decimal("5.01"),
            market_price=Decimal("34.99"),
            description="Simulation locale — coût rendu estimé. Offre CJdropshipping 217 : achat 5,01 USD + livraison 13,32 USD, hors éventuels droits de douane et TVA. Prix de marché médian observé : 34,99 EUR.",
        )

        suggestion = DescriptionSuggestionService.suggest(opportunity)

        self.assertNotIn("simulation locale", suggestion.lower())
        self.assertNotIn("achat 5,01", suggestion.lower())
        self.assertNotIn("prix de marché", suggestion.lower())

    def test_does_not_duplicate_previous_generic_suggestion(self):
        opportunity = ProductOpportunity.objects.create(
            name="Lampe vélo rechargeable USB",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            description="Découvrez Lampe vélo rechargeable USB, un produit pensé pour répondre à vos besoins au quotidien. Une solution pratique à découvrir pour compléter votre équipement.",
        )

        suggestion = DescriptionSuggestionService.suggest(opportunity)

        self.assertEqual(suggestion.lower().count("découvrez"), 1)
        self.assertEqual(suggestion.lower().count("une solution pratique"), 1)

    def test_suggestion_is_customer_facing(self):
        opportunity = ProductOpportunity.objects.create(
            name="Support ordinateur portable",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=80,
            competition_score=40,
            status="approved",
            description="Support pratique pour ordinateur portable.",
            initial_stock=5,
        )

        suggestion = DescriptionSuggestionService.suggest(
            opportunity
        )

        self.assertNotIn(
            "potentiel commercial",
            suggestion.lower(),
        )

        self.assertNotIn(
            "positionnement sur le marché",
            suggestion.lower(),
        )

        self.assertNotIn(
            "cette fiche mérite",
            suggestion.lower(),
        )

        self.assertIn(
            "Support ordinateur portable",
            suggestion,
        )