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
from product_intelligence.services.supplier_offer_research_pipeline import (
    SupplierOfferResearchPipeline,
)
from product_intelligence.services.supplier_offer_shipping import (
    SupplierOfferShippingService,
)
from product_intelligence.services.supplier_offer_visual_matching import (
    SupplierOfferVisualMatchingService,
)


class ComparablePriceRunnerFactoryTests(
    SimpleTestCase
):

    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "os.getenv"
        ),
        return_value="",
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
    def test_builds_comparable_price_runner(
        self,
        ssl_context_class,
        http_client_class,
        openai_class,
        getenv,
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
            runner.research_pipeline,
            SupplierOfferResearchPipeline,
        )

        self.assertIsInstance(
            runner.research_pipeline.shipping_service,
            SupplierOfferShippingService,
        )

        collection_service = (
            runner
            .research_pipeline
            .comparable_price_collection
        )

        self.assertIsInstance(
            collection_service,
            ComparablePriceCollectionService,
        )

        self.assertIsInstance(
            (
                collection_service
                .search_service
            ),
            ComparablePriceSearchService,
        )

        self.assertEqual(
            collection_service.model_name,
            "test-model",
        )

        self.assertEqual(
            runner.destination_country,
            "FR",
        )

    @patch(
        (
            "product_intelligence.services."
            "comparable_price_runner_factory."
            "os.getenv"
        ),
        return_value="",
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
        getenv,
    ):
        runner = (
            ComparablePriceRunnerFactory.build()
        )

        collection_service = (
            runner
            .research_pipeline
            .comparable_price_collection
        )

        self.assertEqual(
            collection_service.model_name,
            ComparablePriceRunnerFactory.DEFAULT_MODEL,
        )

    @patch("product_intelligence.services.comparable_price_runner_factory.SupplierShippingFactory.build")
    @patch("product_intelligence.services.comparable_price_runner_factory.os.getenv")
    @patch("product_intelligence.services.comparable_price_runner_factory.OpenAI")
    @patch("product_intelligence.services.comparable_price_runner_factory.httpx.Client")
    @patch("product_intelligence.services.comparable_price_runner_factory.truststore.SSLContext")
    def test_passes_aw_configuration_to_shipping_factory(self, ssl_context_class, http_client_class, openai_class, getenv, shipping_factory_build):
        getenv.side_effect = lambda key, default="": "test-aw-token" if key == "AW_API_TOKEN" else default
        ComparablePriceRunnerFactory.build(model="test-model")
        self.assertEqual(shipping_factory_build.call_args.kwargs["aw_api_token"], "test-aw-token")



    @patch("product_intelligence.services.comparable_price_runner_factory.ProductVisualMatchingFactory.build")
    @patch("product_intelligence.services.comparable_price_runner_factory.SupplierSearchFactory._build_cj_searcher")
    @patch("product_intelligence.services.comparable_price_runner_factory.SupplierShippingFactory.build")
    @patch("product_intelligence.services.comparable_price_runner_factory.os.getenv")
    @patch("product_intelligence.services.comparable_price_runner_factory.OpenAI")
    @patch("product_intelligence.services.comparable_price_runner_factory.httpx.Client")
    @patch("product_intelligence.services.comparable_price_runner_factory.truststore.SSLContext")
    def test_builds_cj_economic_fallback_when_cj_is_configured(self, ssl_context_class, http_client_class, openai_class, getenv, shipping_factory_build, build_cj_searcher, visual_factory_build):
        getenv.side_effect = lambda key, default="": "cj-api-key" if key == "CJ_API_KEY" else default
        cj_searcher = build_cj_searcher.return_value
        product_visual_matching = visual_factory_build.return_value
        service = ComparablePriceRunnerFactory.build_economic_fallback(model="test-model")
        self.assertIsNotNone(service)
        self.assertIs(service.cj_searcher, cj_searcher)
        self.assertIsInstance(service.research_pipeline, SupplierOfferResearchPipeline)
        visual_factory_build.assert_called_once_with(model="test-model")
        self.assertIsInstance(
            service.visual_matching_service,
            SupplierOfferVisualMatchingService,
        )
        self.assertIs(
            service.visual_matching_service.matching_service,
            product_visual_matching,
        )

    @patch("product_intelligence.services.comparable_price_runner_factory.SupplierSearchFactory._build_cj_searcher")
    @patch("product_intelligence.services.comparable_price_runner_factory.SupplierShippingFactory.build")
    @patch("product_intelligence.services.comparable_price_runner_factory.os.getenv")
    @patch("product_intelligence.services.comparable_price_runner_factory.OpenAI")
    @patch("product_intelligence.services.comparable_price_runner_factory.httpx.Client")
    @patch("product_intelligence.services.comparable_price_runner_factory.truststore.SSLContext")
    def legacy_builds_cj_country_fallback_when_cj_is_configured(self, ssl_context_class, http_client_class, openai_class, getenv, shipping_factory_build, build_cj_searcher):
        getenv.side_effect = lambda key, default="": "cj-api-key" if key == "CJ_API_KEY" else default
        cj_searcher = build_cj_searcher.return_value
        runner = ComparablePriceRunnerFactory.build(model="test-model")
        self.assertIsNotNone(runner.fallback_service)
        self.assertIs(runner.fallback_service.cj_searcher, cj_searcher)
