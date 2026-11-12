import ssl
from unittest.mock import patch

from django.test import SimpleTestCase

from product_intelligence.services.openai_visual_matching_client import (
    OpenAIVisualMatchingClient,
)
from product_intelligence.services.product_visual_matching import (
    ProductVisualMatchingService,
)
from product_intelligence.services.product_visual_matching_factory import (
    ProductVisualMatchingFactory,
)


class ProductVisualMatchingFactoryTests(SimpleTestCase):

    @patch(
        "product_intelligence.services.product_visual_matching_factory.OpenAI"
    )
    @patch(
        "product_intelligence.services.product_visual_matching_factory.httpx.Client"
    )
    @patch(
        "product_intelligence.services.product_visual_matching_factory.truststore.SSLContext"
    )
    def test_builds_visual_matching_service(
        self,
        ssl_context_class,
        http_client_class,
        openai_class,
    ):
        ssl_context = ssl_context_class.return_value
        http_client = http_client_class.return_value
        sdk_client = openai_class.return_value

        service = ProductVisualMatchingFactory.build(
            model="test-model",
        )

        ssl_context_class.assert_called_once_with(
            ssl.PROTOCOL_TLS_CLIENT
        )
        http_client_class.assert_called_once_with(
            verify=ssl_context,
            timeout=120.0,
        )
        openai_class.assert_called_once_with(
            http_client=http_client,
        )
        self.assertIsInstance(
            service,
            ProductVisualMatchingService,
        )
        self.assertIsInstance(
            service.client,
            OpenAIVisualMatchingClient,
        )
        self.assertIs(
            service.client.client,
            sdk_client,
        )
        self.assertEqual(
            service.client.model,
            "test-model",
        )

