from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.product_idea_visual_reference_search import (
    ProductIdeaVisualReferenceSearchService,
    ProductIdeaVisualReferenceSearchResponse,
)


class ProductIdeaVisualReferenceSearchServiceTests(SimpleTestCase):

    def test_searches_visual_references_for_supplier_keywords(self):
        idea = Mock()
        idea.name = "Cycling accessories"
        idea.supplier_search_keywords = [
            "USB rechargeable bike light",
            "reflective cycling vest",
        ]

        client = Mock()
        client.generate.return_value = {"visual_references": [{"supplier_search_keyword": "USB rechargeable bike light", "product_name": "Bike light", "source_title": "Source 1", "source_url": "https://example.com/light", "image_url": "https://example.com/light.jpg"}, {"supplier_search_keyword": "reflective cycling vest", "product_name": "Cycling vest", "source_title": "Source 2", "source_url": "https://example.com/vest", "image_url": "https://example.com/vest.jpg"}]}

        service = ProductIdeaVisualReferenceSearchService(
            client=client,
        )
        result = service.search(product_idea=idea)

        self.assertEqual(len(result["visual_references"]), 2)
        self.assertTrue(
            client.generate.call_args.kwargs["use_web_search"]
        )
        self.assertEqual(
            client.generate.call_args.kwargs["response_model"],
            ProductIdeaVisualReferenceSearchResponse,
        )
        self.assertEqual(
            client.generate.call_args.kwargs["context"]["supplier_search_keywords"],
            idea.supplier_search_keywords,
        )

    def test_rejects_missing_visual_reference_for_supplier_keyword(self):
        from pydantic import ValidationError

        idea = Mock()
        idea.name = "Cycling accessories"
        idea.supplier_search_keywords = [
            "USB rechargeable bike light",
            "reflective cycling vest",
        ]

        client = Mock()
        client.generate.return_value = {
            "visual_references": [{
                "supplier_search_keyword": "USB rechargeable bike light",
                "product_name": "Bike light",
                "source_title": "Source",
                "source_url": "https://example.com/product",
                "image_url": "https://example.com/image.jpg",
            }]
        }

        service = ProductIdeaVisualReferenceSearchService(client=client)

        with self.assertRaises(ValidationError):
            service.search(product_idea=idea)
