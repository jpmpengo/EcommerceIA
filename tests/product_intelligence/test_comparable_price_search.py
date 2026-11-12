from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.comparable_price_search import (
    ComparablePriceSearchResponse,
    ComparablePriceSearchService,
)


class FakeComparablePriceClient:

    def __init__(
        self,
    ):
        self.received_instructions = None
        self.received_context = None
        self.received_response_model = None
        self.received_use_web_search = None

    def generate(
        self,
        instructions,
        context,
        response_model,
        use_web_search=False,
    ):
        self.received_instructions = (
            instructions
        )
        self.received_context = context
        self.received_response_model = (
            response_model
        )
        self.received_use_web_search = (
            use_web_search
        )

        return {
            "comparables": [],
        }


class ComparablePriceSearchResponseTests(SimpleTestCase):

    def test_accepts_optional_image_url(self):
        response = ComparablePriceSearchResponse(
            comparables=[
                {
                    "product_name": "Kit eclairage velo",
                    "observed_price": 39.99,
                    "currency": "EUR",
                    "source_title": "Source test",
                    "source_url": "https://example.com/product",
                    "image_url": "https://example.com/product.jpg",
                    "evidence": "Produit comparable.",
                },
                {
                    "product_name": "Kit sans image",
                    "observed_price": 29.99,
                    "currency": "EUR",
                    "source_title": "Source sans image",
                    "source_url": "https://example.com/product-2",
                    "image_url": None,
                    "evidence": "Produit comparable sans image verifiable.",
                },
            ]
        )

        self.assertEqual(
            response.comparables[0].image_url,
            "https://example.com/product.jpg",
        )
        self.assertIsNone(
            response.comparables[1].image_url,
        )


    def test_accepts_commercial_segment_classification(self):
        response = ComparablePriceSearchResponse(comparables=[{"product_name": "Bague connectee premium", "observed_price": 315.99, "currency": "EUR", "source_title": "Boutique test", "source_url": "https://example.com/ring", "evidence": "Fonctions proches mais gamme premium distincte.", "commercial_segment": "different_segment", "commercial_segment_reason": "Marque premium et positionnement commercial distincts."}])
        comparable = response.comparables[0]
        self.assertEqual(comparable.commercial_segment, "different_segment")
        self.assertIn("premium", comparable.commercial_segment_reason)


class ComparablePriceSearchServiceTests(
    SimpleTestCase
):

    def test_searches_up_to_five_sourced_comparable_prices(
        self,
    ):
        client = FakeComparablePriceClient()

        offer = Mock()
        offer.product_name = (
            "Stackable Storage Box"
        )
        offer.variant_features = {
            "color": "White",
        }
        offer.product_idea.name = (
            "Rangements modulaires "
            "pour petits logements"
        )
        offer.product_idea.countries = [
            "FR",
            "BE",
            "ES",
        ]

        service = (
            ComparablePriceSearchService(
                client=client,
            )
        )

        result = service.search(
            supplier_offer=offer,
        )

        self.assertEqual(
            result,
            {
                "comparables": [],
            },
        )

        self.assertTrue(
            client.received_use_web_search
        )

        self.assertEqual(
            client.received_response_model,
            ComparablePriceSearchResponse,
        )

        self.assertEqual(
            client.received_context[
                "maximum_comparable_prices"
            ],
            5,
        )

        self.assertEqual(
            client.received_context[
                "supplier_product"
            ]["name"],
            "Stackable Storage Box",
        )

        self.assertIn(
            "sources",
            client.received_instructions,
        )

        self.assertIn(
            "domaines distincts",
            client.received_instructions,
        )

    def test_instructions_classify_commercial_segments(self):
        instructions = ComparablePriceSearchService.INSTRUCTIONS
        for term in ("commercial_segment", "commercial_segment_reason", "direct", "different_segment", "unclassified", "prix seul", "caracteristiques verifiables"):
            self.assertIn(term, instructions)
