from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import Supplier, SupplierOffer
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)

from product_intelligence.models import (
    Supplier,
    SupplierOffer,
    ProductOpportunity,
)

from unittest.mock import Mock

from products.models import Product




class SupplierOfferOpportunityServiceTests(TestCase):

    def test_calculates_total_supplier_cost(self):
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

        service = SupplierOfferOpportunityService()

        total_cost = service.total_cost(offer)

        self.assertEqual(
            total_cost,
            Decimal("12.50"),
        )

    def test_calculates_estimated_margin(self):
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

        service = SupplierOfferOpportunityService()

        margin = service.estimated_margin(
            offer,
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            margin,
            Decimal("7.40"),
        )

    def test_calculates_margin_percent(self):
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

        service = SupplierOfferOpportunityService()

        margin_percent = service.margin_percent(
            offer,
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            margin_percent,
            Decimal("59.20"),
        )

    def test_builds_product_opportunity_from_supplier_offer(self):
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

        service = SupplierOfferOpportunityService()

        opportunity = service.create_opportunity(
            offer=offer,
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.name,
            "Produit Test",
        )

        self.assertEqual(
            opportunity.source_name,
            "Fournisseur Test",
        )

        self.assertEqual(
            opportunity.source_url,
            "https://example.com/product",
        )

        self.assertEqual(
            opportunity.supplier_price,
            Decimal("10.00"),
        )

        self.assertEqual(
            opportunity.market_price,
            Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.shipping_cost,
            Decimal("2.50"),
        )   

    def test_created_opportunity_has_commercial_score(self):
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

        service = SupplierOfferOpportunityService()

        opportunity = service.create_opportunity(
            offer=offer,
            market_price=Decimal("19.90"),
        )

        self.assertEqual(
            opportunity.opportunity_score,
            60,
        )
    
    def test_does_not_create_opportunity_below_minimum_margin(self):
        supplier = Supplier.objects.create(
            name="Test Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("15.00"),
            shipping_cost=Decimal("2.00"),
            currency="EUR",
        )

        service = SupplierOfferOpportunityService(
            minimum_margin=Decimal("5.00"),
        )

        result = service.create_opportunity(
            offer=offer,
            market_price=Decimal("20.00"),
        )

        self.assertIsNone(result)

        self.assertEqual(
            ProductOpportunity.objects.count(),
            0,
        )    

    def test_creates_opportunity_when_margin_meets_minimum(self):
        supplier = Supplier.objects.create(
            name="Margin Test Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("15.00"),
            shipping_cost=Decimal("2.00"),
            currency="EUR",
        )

        service = SupplierOfferOpportunityService(
            minimum_margin=Decimal("5.00"),
        )

        result = service.create_opportunity(
            offer=offer,
            market_price=Decimal("22.00"),
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            ProductOpportunity.objects.count(),
            1,
        )

        self.assertEqual(
            result.supplier_price,
            Decimal("15.00"),
        )

        self.assertEqual(
            result.market_price,
            Decimal("22.00"),
        )

        self.assertEqual(
            result.get_estimated_margin(),
            Decimal("5.00"),
        )

    def test_does_not_keep_opportunity_below_minimum_score(self):
        supplier = Supplier.objects.create(
            name="Score Test Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
        )

        service = SupplierOfferOpportunityService(
            minimum_score=70,
        )

        result = service.create_opportunity(
            offer=offer,
            market_price=Decimal("20.00"),
        )

        self.assertIsNone(result)

        self.assertEqual(
            ProductOpportunity.objects.count(),
            0,
        )

    def test_keeps_opportunity_when_score_meets_minimum(self):
        supplier = Supplier.objects.create(
            name="Score Threshold Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
        )

        service = SupplierOfferOpportunityService(
            minimum_score=60,
        )

        result = service.create_opportunity(
            offer=offer,
            market_price=Decimal("20.00"),
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            ProductOpportunity.objects.count(),
            1,
        )

        self.assertEqual(
            result.opportunity_score,
            60,
        )

    def test_does_not_keep_opportunity_below_minimum_stock(self):
        supplier = Supplier.objects.create(
            name="Stock Test Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=50,
        )

        service = SupplierOfferOpportunityService(
            minimum_stock=100,
        )

        result = service.create_opportunity(
            offer=offer,
            market_price=Decimal("20.00"),
        )

        self.assertIsNone(result)

        self.assertEqual(
            ProductOpportunity.objects.count(),
            0,
        )

    def test_keeps_opportunity_when_stock_meets_minimum(self):
        supplier = Supplier.objects.create(
            name="Stock Threshold Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=100,
        )

        service = SupplierOfferOpportunityService(
            minimum_stock=100,
        )

        result = service.create_opportunity(
            offer=offer,
            market_price=Decimal("20.00"),
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            ProductOpportunity.objects.count(),
            1,
        )

        self.assertEqual(
            result.name,
            "Wireless Charger",
        )
    
    def test_evaluates_created_opportunity_with_decision_service(self):
        supplier = Supplier.objects.create(
            name="Decision Test Supplier",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=100,
        )

        decision_service = Mock()

        def evaluate(opportunity):
            return opportunity

        decision_service.evaluate.side_effect = evaluate

        service = SupplierOfferOpportunityService(
            decision_service=decision_service,
        )

        opportunity = service.create_opportunity(
            offer=offer,
            market_price=Decimal("20.00"),
        )

        self.assertIsNotNone(opportunity)

        decision_service.evaluate.assert_called_once_with(
            opportunity
        )

    def test_created_opportunity_keeps_supplier_offer_reference(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("10.00"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        service = SupplierOfferOpportunityService()

        opportunity = service.create_opportunity(
            offer=offer,
            market_price=Decimal("25.00"),
        )

        self.assertEqual(
            opportunity.supplier_offer,
            offer,
        )

    def test_created_opportunity_links_product_to_restock(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit déjà publié",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        old_offer = SupplierOffer.objects.create(
            supplier=supplier,
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

        new_offer = SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id="CJ-123",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.75"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        service = SupplierOfferOpportunityService()

        opportunity = service.create_opportunity(
            offer=new_offer,
            market_price=Decimal("27.90"),
        )

        self.assertEqual(
            opportunity.restock_product,
            product,
        )