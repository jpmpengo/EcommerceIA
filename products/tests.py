from django.test import RequestFactory, TestCase

from .models import Category, Product
from .views import _search_products


class ProductSynonymSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Informatique", slug="informatique")
        cls.mouse = Product.objects.create(
            category=category,
            name="Wireless Mouse Pro",
            description="Accessoire ergonomique",
            price="29.90",
            stock=10,
            is_available=True,
        )
        cls.keyboard = Product.objects.create(
            category=category,
            name="Mechanical Keyboard",
            description="Clavier de bureau",
            price="49.90",
            stock=10,
            is_available=True,
        )
        cls.wired_mouse = Product.objects.create(
            category=category,
            name="Mouse filaire",
            description="Souris USB classique",
            price="12.90",
            stock=10,
            is_available=True,
        )
        cls.factory = RequestFactory()

    def search(self, query):
        request = self.factory.get("/produits/", {"q": query})
        queryset = Product.objects.filter(is_available=True).select_related("category")
        results, _ = _search_products(request, queryset)
        return list(results)

    def test_french_synonym_finds_english_product(self):
        self.assertIn(self.mouse, self.search("souris"))

    def test_english_synonym_finds_french_product(self):
        self.assertIn(self.keyboard, self.search("keyboard"))

    def test_multiword_synonym_without_false_positive(self):
        results = self.search("souris sans fil")
        self.assertIn(self.mouse, results)
        self.assertNotIn(self.wired_mouse, results)

    def test_multiple_intentions_keep_and_semantics(self):
        self.assertNotIn(self.keyboard, self.search("souris sans fil"))
