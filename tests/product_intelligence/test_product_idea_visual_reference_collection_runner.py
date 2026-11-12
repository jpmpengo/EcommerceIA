from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from product_intelligence.services.product_idea_visual_reference_collection_runner import (
    ProductIdeaVisualReferenceCollectionRunner,
)


class ProductIdeaVisualReferenceCollectionRunnerTests(SimpleTestCase):

    @patch("product_intelligence.services.product_idea_visual_reference_collection_runner.ProductIdeaVisualReferenceCollectionService")
    @patch("product_intelligence.services.product_idea_visual_reference_collection_runner.ProductIdeaVisualReferenceSearchService")
    @patch("product_intelligence.services.product_idea_visual_reference_collection_runner.OpenAIClient")
    @patch("product_intelligence.services.product_idea_visual_reference_collection_runner.OpenAI")
    @patch("product_intelligence.services.product_idea_visual_reference_collection_runner.httpx.Client")
    @patch("product_intelligence.services.product_idea_visual_reference_collection_runner.truststore.SSLContext")
    def test_collects_visual_references_for_existing_idea(self, ssl_context_class, http_client_class, openai_class, openai_client_class, search_service_class, collection_service_class):
        idea = Mock()
        collection_service = collection_service_class.return_value
        collection_service.collect.return_value = [Mock(), Mock()]

        result = ProductIdeaVisualReferenceCollectionRunner.collect(
            product_idea=idea,
            model="test-model",
        )

        collection_service.collect.assert_called_once_with(
            product_idea=idea,
        )
        self.assertEqual(len(result), 2)
