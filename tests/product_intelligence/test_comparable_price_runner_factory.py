import ssl
from unittest.mock import patch

from django.test import SimpleTestCase

from product_intelligence.services.comparable_price_collection import (
    ComparablePriceCollectionService,
)
from product_intelligence.services.comparable_price_collection_runner import (
    ComparablePriceCollectionRunner,
)
from product_intelligence.services.comparable_price_runner_factory import (
    ComparablePriceRunnerFactory,
)
from product_intelligence.services.comparable_price_search import (
    ComparablePriceSearchService,
)


class ComparablePriceRunnerFactoryTests(
    SimpleTestCase
):

    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "OpenAI"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "httpx.Client"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "truststore.SSLContext"
        )
    )
    def test_builds_comparable_price_runner(
        self,
        ssl_context_class,
        http_client_class,
        openai_class,
    ):
        ssl_context = (
            ssl_context_class.return_value
        )

        http_client = (
            http_client_class.return_value
        )

        runner = (
            ComparablePriceRunnerFactory.build(
                model="test-model",
            )
        )

        ssl_context_class.assert_called_once_with(
            ssl.PROTOCOL_TLS_CLIENT
        )

        http_client_class.assert_called_once_with(
            verify=ssl_context,
            timeout=60.0,
        )

        openai_class.assert_called_once_with(
            http_client=http_client,
        )

        self.assertIsInstance(
            runner,
            ComparablePriceCollectionRunner,
        )

        self.assertIsInstance(
            runner.collection_service,
            ComparablePriceCollectionService,
        )

        self.assertIsInstance(
            (
                runner
                .collection_service
                .search_service
            ),
            ComparablePriceSearchService,
        )

        self.assertEqual(
            runner.collection_service.model_name,
            "test-model",
        )

    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "OpenAI"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "httpx.Client"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "truststore.SSLContext"
        )
    )
    def test_uses_default_model(
        self,
        ssl_context_class,
        http_client_class,
        openai_class,
    ):
        runner = (
            ComparablePriceRunnerFactory.build()
        )

        self.assertEqual(
            runner.collection_service.model_name,
            ComparablePriceRunnerFactory.DEFAULT_MODEL,
        )