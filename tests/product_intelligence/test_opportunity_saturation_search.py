from unittest.mock import Mock
from django.test import SimpleTestCase
from product_intelligence.services.opportunity_saturation_search import OpportunitySaturationSearchService, OpportunitySaturationSearchResponse

class OpportunitySaturationSearchTests(SimpleTestCase):
    def test_search_uses_web_and_targets_fr_be_es(self):
        client = Mock()
        client.generate.return_value = {"level": "indeterminate", "justification": "Preuves insuffisantes", "sources": []}
        service = OpportunitySaturationSearchService(client=client)
        service.search(product_name="Organisateur sous-evier", product_attributes={"material": "metal"})
        kwargs = client.generate.call_args.kwargs
        self.assertTrue(kwargs["use_web_search"])
        self.assertEqual(kwargs["response_model"], OpportunitySaturationSearchResponse)
        self.assertEqual(kwargs["context"]["target_countries"], ["FR", "BE", "ES"])
        self.assertEqual(kwargs["context"]["product"]["name"], "Organisateur sous-evier")
        self.assertEqual(kwargs["context"]["product"]["attributes"], {"material": "metal"})

    def test_search_without_sources_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "low", "justification": "Peu de concurrents", "sources": []}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_with_invalid_source_url_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "low", "justification": "Concurrence faible", "sources": ["source non verifiable"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_with_only_invalid_urls_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "moderate", "justification": "Plusieurs vendeurs", "sources": ["pas une URL", "ftp://example.com/produit", "https:///produit"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_without_justification_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "low", "justification": "", "sources": ["https://example.com/produit"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_with_valid_source_and_justification_preserves_level(self):
        client = Mock()
        client.generate.return_value = {"level": "moderate", "justification": "Plusieurs offres concurrentes observees", "sources": ["https://www.amazon.fr/produit-test"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "moderate")

    def test_search_with_placeholder_source_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "low", "justification": "Concurrence faible", "sources": ["https://example.com/produit"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_with_homepage_only_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "low", "justification": "Concurrence faible", "sources": ["https://www.amazon.fr/"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_with_search_results_page_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "low", "justification": "Plusieurs offres trouvees", "sources": ["https://www.amazon.fr/s?k=organisateur"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_same_seller_multiple_urls_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Trois offres concurrentes", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b", "https://www.amazon.fr/produit-c"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_saturation_with_duplicate_sellers_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Trois offres concurrentes", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b", "https://www.amazon.fr/produit-c"], "sellers": ["Vendeur A", "Vendeur A", "Vendeur A"]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_saturation_with_seller_name_variants_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs observes", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b"], "sellers": ["Vendeur A", " vendeur a "]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_response_preserves_structured_competitor_evidence(self):
        response = OpportunitySaturationSearchResponse(level="moderate", justification="Offre observee", competitor_evidence=[{"offer_url": "https://www.amazon.fr/produit-a", "seller_name": "Vendeur A", "country": "FR"}])
        evidence = response.competitor_evidence[0]
        self.assertEqual(evidence.offer_url, "https://www.amazon.fr/produit-a")
        self.assertEqual(evidence.seller_name, "Vendeur A")
        self.assertEqual(evidence.country, "FR")

    def test_search_high_without_structured_evidence_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs observes", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b"], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": []}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_with_one_evidenced_seller_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs annonces", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b"], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": "https://www.amazon.fr/produit-a", "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": "https://www.amazon.fr/produit-b", "seller_name": "Vendeur A", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_with_unreferenced_evidence_urls_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs observes", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b"], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": "https://www.amazon.fr/autre-produit-a", "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": "https://www.amazon.fr/autre-produit-b", "seller_name": "Vendeur B", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_with_same_offer_url_for_two_sellers_returns_indeterminate(self):
        client = Mock()
        url = "https://www.amazon.fr/produit-a"
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs observes", "sources": [url], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": url, "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": url, "seller_name": "Vendeur B", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_with_unmatched_seller_urls_returns_indeterminate(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs observes", "sources": ["https://www.amazon.fr/produit-a", "https://www.amazon.fr/produit-b"], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": "https://www.amazon.fr/produit-a", "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": "https://www.amazon.fr/produit-b", "seller_name": "Vendeur C", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "high")
        self.assertEqual(result["sellers"], ["Vendeur A", "Vendeur C"])

    def test_search_high_with_two_distinct_evidenced_sellers_preserves_level(self):
        client = Mock()
        url_a = "https://www.amazon.fr/produit-a"
        url_b = "https://www.cdiscount.com/produit-b"
        client.generate.return_value = {"level": "high", "justification": "Deux offres concurrentes distinctes", "sources": [url_a, url_b], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": url_a, "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": url_b, "seller_name": "Vendeur B", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "high")

    def test_search_high_with_invalid_evidence_country_returns_indeterminate(self):
        client = Mock()
        url_a = "https://www.amazon.fr/produit-a"
        url_b = "https://www.cdiscount.com/produit-b"
        client.generate.return_value = {"level": "high", "justification": "Deux offres observees", "sources": [url_a, url_b], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": url_a, "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": url_b, "seller_name": "Vendeur B", "country": "US"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_with_empty_evidence_seller_returns_indeterminate(self):
        client = Mock()
        urls = ["https://www.amazon.fr/produit-a", "https://www.cdiscount.com/produit-b", "https://www.fnac.com/produit-c"]
        client.generate.return_value = {"level": "high", "justification": "Offres concurrentes observees", "sources": urls, "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": [{"offer_url": urls[0], "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": urls[1], "seller_name": "Vendeur B", "country": "FR"}, {"offer_url": urls[2], "seller_name": "", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "indeterminate")

    def test_search_high_with_empty_evidence_url_returns_indeterminate(self):
        client = Mock()
        urls = ["https://www.amazon.fr/produit-a", "https://www.cdiscount.com/produit-b"]
        client.generate.return_value = {"level": "high", "justification": "Deux offres concurrentes observees", "sources": urls, "sellers": ["Vendeur A", "Vendeur B", "Vendeur C"], "competitor_evidence": [{"offer_url": urls[0], "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": urls[1], "seller_name": "Vendeur B", "country": "FR"}, {"offer_url": "", "seller_name": "Vendeur C", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "high")
        self.assertEqual(len(result["competitor_evidence"]), 2)
        self.assertEqual(result["sellers"], ["Vendeur A", "Vendeur B"])

    def test_search_high_with_homepage_evidence_url_returns_indeterminate(self):
        client = Mock()
        urls = ["https://www.amazon.fr/produit-a", "https://www.cdiscount.com/produit-b", "https://www.fnac.com/"]
        client.generate.return_value = {"level": "high", "justification": "Trois vendeurs observes", "sources": urls, "sellers": ["Vendeur A", "Vendeur B", "Vendeur C"], "competitor_evidence": [{"offer_url": urls[0], "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": urls[1], "seller_name": "Vendeur B", "country": "FR"}, {"offer_url": urls[2], "seller_name": "Vendeur C", "country": "FR"}]}
        service = OpportunitySaturationSearchService(client=client)
        result = service.search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "high")
        self.assertEqual(len(result["competitor_evidence"]), 2)
        self.assertEqual(result["sellers"], ["Vendeur A", "Vendeur B"])
    def test_search_high_rebuilds_sellers_from_evidence(self):
        client = Mock()
        url_a = "https://www.amazon.fr/produit-a"
        url_b = "https://www.cdiscount.com/produit-b"
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs distincts observes", "sources": [url_a, url_b], "sellers": ["Vendeur A", "Vendeur errone"], "competitor_evidence": [{"offer_url": url_a, "seller_name": "Vendeur A", "country": "FR"}, {"offer_url": url_b, "seller_name": "Vendeur B", "country": "FR"}]}
        result = OpportunitySaturationSearchService(client=client).search(product_name="Organisateur sous-evier", product_attributes={})
        self.assertEqual(result["level"], "high")
        self.assertEqual(result["sellers"], ["Vendeur A", "Vendeur B"])

    def test_search_preserves_original_level_and_validation_reason(self):
        client = Mock()
        client.generate.return_value = {"level": "high", "justification": "Deux vendeurs observes", "sources": ["https://www.amazon.fr/produit-a", "https://www.cdiscount.com/produit-b"], "sellers": ["Vendeur A", "Vendeur B"], "competitor_evidence": []}
        result = OpportunitySaturationSearchService(client=client).search(product_name="Produit test", product_attributes={})
        self.assertEqual(result["original_level"], "high")
        self.assertEqual(result["level"], "indeterminate")
        self.assertTrue(result["validation_reason"])

    def test_search_high_accepts_trailing_slash_variant(self):
        a="https://vendeur-a.fr/products/a"
        b="https://vendeur-b.es/products/b"
        client=Mock()
        client.generate.return_value={"level":"high","justification":"Deux vendeurs distincts","sources":[a,b],"competitor_evidence":[{"offer_url":a,"seller_name":"A","country":"FR"},{"offer_url":b+"/","seller_name":"B","country":"ES"}]}
        result=OpportunitySaturationSearchService(client).search("Produit",{})
        self.assertEqual(result["level"],"high")

    def test_search_high_accepts_product_query_url(self):
        a="https://vendeur-a.fr/products/a"
        b="https://avlo-deerlijk.be/?product=article-123"
        client=Mock()
        client.generate.return_value={"level":"high","justification":"Deux vendeurs distincts","sources":[a,b],"competitor_evidence":[{"offer_url":a,"seller_name":"A","country":"FR"},{"offer_url":b,"seller_name":"B","country":"BE"}]}
        result=OpportunitySaturationSearchService(client).search("Produit",{})
        self.assertEqual(result["level"],"high")


    def test_search_high_ignores_invalid_homepage_when_two_valid_sellers_remain(self):
        client = Mock()
        a = "https://vendeur-a.fr/products/masque-led"
        b = "https://vendeur-b.be/products/masque-led"
        bad = "https://vendeur-c.fr/"
        client.generate.return_value = {"level": "high", "justification": "Concurrence elevee", "sources": [a, b, bad], "sellers": ["A", "B", "C"], "competitor_evidence": [{"offer_url": a, "seller_name": "A", "country": "FR"}, {"offer_url": b, "seller_name": "B", "country": "BE"}, {"offer_url": bad, "seller_name": "C", "country": "FR"}]}
        result = OpportunitySaturationSearchService(client).search("Masque LED", {})
        self.assertEqual(result["level"], "high")
        self.assertEqual(len(result["competitor_evidence"]), 2)
        self.assertEqual(result["sellers"], ["A", "B"])
