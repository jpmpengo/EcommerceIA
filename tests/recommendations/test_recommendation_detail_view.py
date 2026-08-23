from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import (
    ProductOpportunity,
    Supplier,
    SupplierOffer,
)

from products.models import Product

from unittest.mock import Mock, patch

from django.core.files.base import ContentFile

from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.models import Group



class RecommendationDetailViewTests(TestCase):

    def setUp(self):
        self.emma_user = (
            get_user_model()
            .objects.create_user(
                username="emma_operator",
                email="emma@example.com",
                password=(
                    "MotDePasse-Test-2026!"
                ),
            )
        )

        emma_group = Group.objects.create(
            name="Emma Operators"
        )

        self.emma_user.groups.add(
            emma_group
        )

        self.client.login(
            username="emma_operator",
            password=(
                "MotDePasse-Test-2026!"
            ),
        )

    def test_detail_exposes_suggested_stock(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            supplier_offer=offer,
            status="approved",
            initial_stock=0,
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(
            response.context["suggested_stock"],
            10,
        )

    def test_detail_identifies_restock_opportunity(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.context["is_restock"]
        )

        self.assertEqual(
            response.context["restock_product"],
            product,
        )

    def test_detail_shows_restock_action(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Réapprovisionner",
        )

    def test_restock_action_increases_existing_product_stock(self):
        product = Product.objects.create(
            name="Wireless Charger",
            description="Produit existant",
            price=Decimal("27.90"),
            stock=0,
            is_available=True,
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.75"),
            market_price=Decimal("27.90"),
            status="approved",
            restock_product=product,
        )

        product_count_before = Product.objects.count()

        response = self.client.post(
            reverse(
                "recommendations:restock",
                args=[opportunity.id],
            ),
            {
                "quantity": 10,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        product.refresh_from_db()

        self.assertEqual(
            product.stock,
            10,
        )

        self.assertEqual(
            Product.objects.count(),
            product_count_before,
        )

    def test_detail_exposes_supplier_image_url(self):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id="CJ-IMAGE-001",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
            image_url=(
                "https://example.com/"
                "wireless-charger.jpg"
            ),
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            supplier_offer=offer,
            status="approved",
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(
            response.context["suggested_image_url"],
            "https://example.com/wireless-charger.jpg",
        )

    @patch("recommendations.views.httpx.get")
    def test_apply_supplier_image_downloads_and_saves_image(
        self,
        mock_get,
    ):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://example.com",
            supplier_type="dropshipper",
        )

        offer = SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id="CJ-IMAGE-003",
            product_name="Wireless Charger",
            purchase_price=Decimal("4.53"),
            shipping_cost=Decimal("0.00"),
            currency="EUR",
            stock=250,
            image_url=(
                "https://example.com/"
                "wireless-charger.jpg"
            ),
        )

        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            supplier_offer=offer,
            status="approved",
        )

        response_mock = Mock()
        response_mock.content = b"fake-image-content"
        response_mock.headers = {
            "content-type": "image/jpeg",
        }
        response_mock.raise_for_status.return_value = None

        mock_get.return_value = response_mock

        response = self.client.post(
            reverse(
                "recommendations:apply_supplier_image",
                args=[opportunity.id],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        opportunity.refresh_from_db()

        self.assertTrue(
            bool(opportunity.image)
        )

        mock_get.assert_called_once()

        args, kwargs = mock_get.call_args

        self.assertEqual(
            args[0],
            offer.image_url,
        )

        self.assertEqual(
            kwargs["timeout"],
            30.0,
        )

        self.assertIn(
            "verify",
            kwargs,
        )

    def test_detail_labels_unreliable_margin_as_provisional(
        self,
    ):
        opportunity = (
            ProductOpportunity.objects.create(
                name="Produit aux frais inconnus",
                source_name="Test",
                supplier_price=Decimal(
                    "10.00"
                ),
                market_price=Decimal(
                    "30.00"
                ),
                shipping_cost=Decimal(
                    "0.00"
                ),
                shipping_cost_is_known=False,
                other_costs=Decimal(
                    "0.00"
                ),
                demand_score=70,
                competition_score=40,
                status="approved",
            )
        )

        response = self.client.get(
            reverse(
                "recommendations:detail",
                args=[opportunity.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Marge provisoire estimée",
        )
