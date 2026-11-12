from django.test import SimpleTestCase

from product_intelligence.services.product_idea_evidence_verification import (
    ProductIdeaEvidenceVerificationService,
)


class ProductIdeaEvidenceVerificationServiceTests(SimpleTestCase):

    def test_valid_url_alone_does_not_verify_evidence(self):
        service = ProductIdeaEvidenceVerificationService()

        result = service.verify(
            source_url="https://example.com/source",
            metric="search_trend",
            value="documented growth",
        )

        self.assertFalse(result.is_verified)

    def test_accessible_page_without_growth_evidence_is_not_verified(self):
        class FakeResponse:
            status_code = 200
            text = "Catalogue de produits sans preuve de croissance"
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="documented growth")
        self.assertFalse(result.is_verified)

    def test_verify_fetches_source_page(self):
        class FakeResponse:
            def raise_for_status(self):
                pass
            text = "Catalogue sans preuve de croissance"

        class FakeHttpClient:
            def __init__(self):
                self.requested_urls = []
            def get(self, url):
                self.requested_urls.append(url)
                return FakeResponse()

        http_client = FakeHttpClient()
        service = ProductIdeaEvidenceVerificationService(http_client=http_client)
        service.verify(source_url="https://example.com/source", metric="search_trend", value="documented growth")
        self.assertEqual(http_client.requested_urls, ["https://example.com/source"])

    def test_documented_growth_is_verified(self):
        class FakeResponse:
            text = "Monthly searches increased from 100 in January 2026 to 150 in March 2026, a 50% growth."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from January to March 2026")
        self.assertTrue(result.is_verified)

    def test_calculates_growth_from_source_values(self):
        class FakeResponse:
            text = "Monthly searches increased from 200 in January 2026 to 260 in March 2026."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="30% growth from January to March 2026")
        self.assertTrue(result.is_verified)

    def test_growth_with_different_months(self):
        class FakeResponse:
            text = "Monthly searches increased from 80 in April 2026 to 120 in June 2026."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from April to June 2026")
        self.assertTrue(result.is_verified)

    def test_rejects_mismatched_growth_periods(self):
        class FakeResponse:
            text = "Monthly searches increased from 100 in January 2026 to 150 in March 2026."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from April to June 2026")
        self.assertFalse(result.is_verified)

    def test_rejects_mismatched_growth_years(self):
        class FakeResponse:
            text = "Monthly searches increased from 100 in January 2026 to 150 in March 2026."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from January to March 2025")
        self.assertFalse(result.is_verified)

    def test_accepts_documented_growth_in_2025(self):
        class FakeResponse:
            text = "Monthly searches increased from 100 in January 2025 to 150 in March 2025."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from January to March 2025")
        self.assertTrue(result.is_verified)

    def test_accepts_growth_across_two_years(self):
        class FakeResponse:
            text = "Monthly searches increased from 100 in November 2025 to 150 in February 2026."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from November 2025 to February 2026")
        self.assertTrue(result.is_verified)

    def test_rejects_reverse_chronological_period(self):
        class FakeResponse:
            text = "Monthly searches increased from 100 in February 2026 to 150 in November 2025."
            def raise_for_status(self):
                pass

        class FakeHttpClient:
            def get(self, url):
                return FakeResponse()

        service = ProductIdeaEvidenceVerificationService(http_client=FakeHttpClient())
        result = service.verify(source_url="https://example.com/source", metric="search_trend", value="50% growth from February 2026 to November 2025")
        self.assertFalse(result.is_verified)
