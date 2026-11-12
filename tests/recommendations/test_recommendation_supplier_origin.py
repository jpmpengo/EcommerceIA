from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from product_intelligence.models import ProductOpportunity, Supplier, SupplierOffer


User = get_user_model()


class RecommendationSupplierOriginTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="emma_supplier_origin",
            password="MotDePasse-Test-2026!",
        )
        emma_group = Group.objects.create(name="Emma Operators")
        self.user.groups.add(emma_group)
        self.client.login(
            username="emma_supplier_origin",
            password="MotDePasse-Test-2026!",
        )

    def _create_opportunity(self, stock_country):
        supplier = Supplier.objects.create(
            name="CJdropshipping",
            country="CN",
            website="https://cjdropshipping.com",
            supplier_type="dropshipper",
        )
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            product_name="Produit test CJ",
            purchase_price=Decimal("10.00"),
            currency="USD",
            stock=100,
            stock_country=stock_country,
        )
        return ProductOpportunity.objects.create(
            name="Produit test CJ",
            source_name="CJdropshipping",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            shipping_cost=Decimal("5.00"),
            shipping_cost_is_known=True,
            other_costs=Decimal("0.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            supplier_offer=offer,
        )

    def test_detail_displays_supplier_and_known_stock_country(self):
        opportunity = self._create_opportunity("CN")

        response = self.client.get(
            reverse("recommendations:detail", args=[opportunity.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fournisseur")
        self.assertContains(response, "CJdropshipping")
        self.assertContains(response, "Origine")
        self.assertContains(response, "CN")

    def test_detail_displays_unknown_origin_when_stock_country_is_empty(self):
        opportunity = self._create_opportunity("")

        response = self.client.get(
            reverse("recommendations:detail", args=[opportunity.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Origine non renseignée")
