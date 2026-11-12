from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product


class ProductSearchTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.computing = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )
        cls.home = Category.objects.create(
            name="Maison",
            slug="maison",
        )

        cls.mouse = Product.objects.create(
            category=cls.computing,
            name="Souris ergonomique",
            description="Souris sans fil silencieuse pour le bureau.",
            price=Decimal("29.90"),
            stock=10,
            is_available=True,
        )
        cls.keyboard = Product.objects.create(
            category=cls.computing,
            name="Clavier mécanique",
            description="Clavier compact pour ordinateur.",
            price=Decimal("59.90"),
            stock=5,
            is_available=True,
        )
        cls.organizer = Product.objects.create(
            category=cls.home,
            name="Organisateur multifonction",
            description="Rangement pratique pour la cuisine.",
            price=Decimal("19.90"),
            stock=8,
            is_available=True,
        )
        cls.hidden = Product.objects.create(
            category=cls.computing,
            name="Souris indisponible",
            description="Ancien modèle sans fil.",
            price=Decimal("9.90"),
            stock=0,
            is_available=False,
        )

    def test_searches_product_name(self):
        response = self.client.get(
            reverse("products:product_list"),
            {"q": "souris"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Souris ergonomique")
        self.assertNotContains(response, "Clavier mécanique")
        self.assertNotContains(response, "Souris indisponible")

    def test_searches_description(self):
        response = self.client.get(
            reverse("products:product_list"),
            {"q": "cuisine"},
        )

        self.assertContains(response, "Organisateur multifonction")
        self.assertNotContains(response, "Souris ergonomique")

    def test_searches_category_name(self):
        response = self.client.get(
            reverse("products:product_list"),
            {"q": "informatique"},
        )

        self.assertContains(response, "Souris ergonomique")
        self.assertContains(response, "Clavier mécanique")
        self.assertNotContains(response, "Organisateur multifonction")

    def test_multiple_terms_make_search_more_precise(self):
        response = self.client.get(
            reverse("products:product_list"),
            {"q": "souris silencieuse"},
        )

        self.assertContains(response, "Souris ergonomique")
        self.assertNotContains(response, "Clavier mécanique")

    def test_category_search_stays_inside_category(self):
        response = self.client.get(
            reverse(
                "products:products_by_category",
                args=[self.computing.slug],
            ),
            {"q": "souris"},
        )

        self.assertContains(response, "Souris ergonomique")
        self.assertNotContains(response, "Organisateur multifonction")

    def test_catalog_uses_six_columns_on_large_screens(self):
        response = self.client.get(
            reverse("products:product_list")
        )

        self.assertContains(response, "width: 16.666667%")
