from django.test import SimpleTestCase
from product_intelligence.services.product_idea_evidence_verification import ProductIdeaEvidenceVerificationService as V


class ProductIdeaEvidenceProductMatchingTests(SimpleTestCase):
    def test_rejects_growth_for_different_product(self):
        self.assertFalse(V._verify_sales_growth('sales of electric bicycles rose 149%', 'sales of beauty devices rose 149%'))

    def test_rejects_different_growth_percentage(self):
        self.assertFalse(V._verify_sales_growth('smart ring unit volume has grown 195%', 'smart ring unit volume has grown 88%'))

    def test_rejects_different_product_with_sales_after_name(self):
        content = 'sales of electric bicycles rose 149% year over year between january and september 2025'
        claim = 'makeon beauty-device sales rose 149% year over year between january and september 2025'
        self.assertFalse(V._verify_sales_growth(content, claim))
