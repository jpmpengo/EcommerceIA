from decimal import Decimal

from django.test import TestCase

from products.models import Category
from product_intelligence.models import ProductOpportunity

from dashboard.services.category_suggestion_service import (
    CategorySuggestionService,
)


class CategorySuggestionServiceTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )
        self.audio = Category.objects.create(
            name="Audio",
            slug="audio",
        )

    def test_suggests_matching_category(self):
        opportunity = ProductOpportunity.objects.create(
            name="Support ordinateur portable",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Support réglable pour ordinateur portable avec une description suffisamment détaillée "
                        " pour permettre sa publication dans la boutique.",
            initial_stock=5,
        )

        category = (
            CategorySuggestionService.suggest(
                opportunity
            )
        )

        self.assertEqual(
            category,
            self.category,
        )

    def test_suggests_informatique_for_mouse(self):
        opportunity = ProductOpportunity.objects.create(
            name="Souris Logitech MX",
            source_name="Amazon",
            supplier_price=Decimal("35.00"),
            market_price=Decimal("79.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("2.00"),
            demand_score=85,
            competition_score=35,
            status="approved",
            description="Souris ergonomique sans fil avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=None,
        )

        category = CategorySuggestionService.suggest(
            opportunity
        )

        self.assertIsNotNone(category)

        self.assertEqual(
            category.name,
            "Informatique",
        )

    def test_suggests_electronics_for_wireless_charger(self):
        from decimal import Decimal

        from product_intelligence.models import ProductOpportunity
        from products.models import Category

        electronics = Category.objects.create(
            name="Électronique",
        )

        opportunity = ProductOpportunity.objects.create(
            name="Cross-Border 10W Mirror Wireless Charger Fast Charge",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            description=(
                "Chargeur sans fil pratique pour smartphone."
            ),
        )

        category = CategorySuggestionService.suggest(
            opportunity
        )

        self.assertEqual(
            category,
            electronics,
        )

    def test_prefers_existing_category_from_product_idea_category_path(self):
        from product_intelligence.models import ProductIdea, Supplier, SupplierOffer

        idea = ProductIdea.objects.create(
            name="Accessoires audio nomades",
            customer_problem="Écouter en mobilité.",
            target_customer="Utilisateurs mobiles.",
            reason_to_study="Demande documentée.",
            countries=["FR"],
            category_path=["Électronique", "Audio"],
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
            product_name="Portable Wireless BT Device X200",
            purchase_price=Decimal("8.00"),
        )
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=supplier.name,
            supplier_price=Decimal("8.00"),
            market_price=Decimal("30.00"),
            supplier_offer=offer,
        )

        category = CategorySuggestionService.suggest(opportunity)

        self.assertEqual(category, self.audio)

    def test_uses_product_idea_name_when_supplier_name_is_not_commercial(self):
        from product_intelligence.models import ProductIdea, Supplier, SupplierOffer

        garden = Category.objects.create(
            name="Jardin",
            slug="jardin",
        )
        idea = ProductIdea.objects.create(
            name="Kits de jardinage urbain pour balcon",
            customer_problem="Cultiver sur un petit balcon.",
            target_customer="Habitants urbains.",
            reason_to_study="Besoin documenté.",
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
            product_name="Thickened Resin Hanging Planter Basket White 20.5x12.5cm",
            purchase_price=Decimal("4.00"),
        )
        opportunity = ProductOpportunity.objects.create(
            name=offer.product_name,
            source_name=supplier.name,
            supplier_price=Decimal("4.00"),
            market_price=Decimal("20.00"),
            supplier_offer=offer,
        )

        category = CategorySuggestionService.suggest(opportunity)

        self.assertEqual(category, garden)

    def test_suggests_informatique_for_gaming_mouse_pad(
        self,
    ):
        opportunity = ProductOpportunity.objects.create(
            name=(
                "Table Pad Line Gaming Mouse Mat "
                "300x800x2MM FW6"
            ),
            source_name="CJdropshipping",
            supplier_price=Decimal("0.85"),
            market_price=Decimal("51.96"),
            description="",
        )

        category = (
            CategorySuggestionService.suggest(
                opportunity
            )
        )

        self.assertEqual(
            category,
            self.category,
        )

    def test_suggests_home_and_kitchen_for_ceramic_mug(
        self,
    ):
        home_and_kitchen = Category.objects.get(
            name="Maison & Cuisine",
        )

        opportunity = ProductOpportunity.objects.create(
            name=(
                "Ceramic Coffee Cup Ceramic Mug "
                "Blue And Brown 200ml"
            ),
            source_name="CJdropshipping",
            supplier_price=Decimal("2.81"),
            market_price=Decimal("17.00"),
            description="",
        )

        category = (
            CategorySuggestionService.suggest(
                opportunity
            )
        )

        self.assertEqual(
            category,
            home_and_kitchen,
        )

    def test_suggests_fashion_for_canvas_tote_bag(
        self,
    ):
        fashion = Category.objects.get(
            name="Mode & Accessoires",
        )

        opportunity = ProductOpportunity.objects.create(
            name="Cotton Canvas Tote Bag 15 x 16 in",
            source_name="Printful",
            supplier_price=Decimal("9.00"),
            market_price=Decimal("17.90"),
            description="",
        )

        category = (
            CategorySuggestionService.suggest(
                opportunity
            )
        )

        self.assertEqual(
            category,
            fashion,
        )
