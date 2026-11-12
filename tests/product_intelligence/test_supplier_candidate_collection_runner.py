import os
from unittest.mock import (
    Mock,
    patch,
)

from django.test import SimpleTestCase

from product_intelligence.services.supplier_candidate_collection_runner import (
    SupplierCandidateCollectionRunner,
)
from product_intelligence.services.supplier_offer_visual_matching import (
    SupplierOfferVisualMatchingService,
)


class SupplierCandidateCollectionRunnerTests(
    SimpleTestCase
):

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "cj-api-key",
            "PRINTFUL_API_TOKEN": "",
            "AW_API_TOKEN": "aw-test-token",
            "AW_API_BASE_URL": "https://api.aiku.io",
        },
        clear=True,
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_candidate_collection_runner."
            "ProductVisualMatchingFactory.build"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_candidate_collection_runner."
            "SupplierSearchFactory.build"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_candidate_collection_runner."
            "httpx.Client"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_candidate_collection_runner."
            "truststore.SSLContext"
        )
    )
    def test_collects_with_configured_suppliers(
        self,
        ssl_context_class,
        http_client_class,
        factory_build,
        visual_factory_build,
    ):
        idea = Mock()
        idea.id = 42
        idea.status = "selected"

        ssl_context = (
            ssl_context_class.return_value
        )

        http_client = Mock()
        (
            http_client_class
            .return_value
            .__enter__
            .return_value
        ) = http_client

        searcher = Mock()
        searcher.search_for_idea.return_value = []

        factory_build.return_value = [
            searcher,
        ]

        visual_matching_service = (
            visual_factory_build.return_value
        )

        summary = (
            SupplierCandidateCollectionRunner
            .collect(
                product_idea=idea,
            )
        )

        factory_build.assert_called_once_with(
            http_client=http_client,
            cj_api_key="cj-api-key",
            printful_api_token="",
            eprolo_api_key="",
            eprolo_api_secret="",
            eprolo_api_base_url=None,
            eprolo_max_catalog_pages=5,
            aw_api_token="aw-test-token",
            aw_api_base_url="https://api.aiku.io",
        )

        visual_factory_build.assert_called_once()

        self.assertEqual(
            summary,
            {
                "product_idea_id": 42,
                "suppliers_searched": 1,
                "offers_found": 0,
                "offers_by_supplier": {},
                "suppliers_unavailable": {},
            },
        )

        http_client_class.assert_called_once_with(
            verify=ssl_context,
            timeout=60.0,
        )

    @patch.dict(
        os.environ,
        {},
        clear=True,
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_candidate_collection_runner."
            "httpx.Client"
        )
    )
    def test_rejects_when_no_supplier_is_configured(
        self,
        http_client_class,
    ):
        idea = Mock()
        idea.status = "selected"

        with self.assertRaisesMessage(
            ValueError,
            (
                "Aucun fournisseur "
                "n’est configuré."
            ),
        ):
            (
                SupplierCandidateCollectionRunner
                .collect(
                    product_idea=idea,
                )
            )

        http_client_class.assert_not_called()

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "cj-api-key",
            "PRINTFUL_API_TOKEN": "",
            "AW_API_TOKEN": "",
        },
        clear=True,
    )
    @patch("product_intelligence.services.supplier_candidate_collection_runner.SupplierOfferVisualMatchingService")
    @patch(
        "product_intelligence.services.supplier_candidate_collection_runner.ProductVisualMatchingFactory.build"
    )
    @patch(
        "product_intelligence.services.supplier_candidate_collection_runner.SupplierSearchFactory.build"
    )
    @patch(
        "product_intelligence.services.supplier_candidate_collection_runner.httpx.Client"
    )
    @patch(
        "product_intelligence.services.supplier_candidate_collection_runner.truststore.SSLContext"
    )
    def legacy_uses_cn_fallback_when_cj_europe_returns_no_offer(
        self,
        ssl_context_class,
        http_client_class,
        factory_build,
        visual_factory_build,
        visual_service_class,
    ):
        idea = Mock()
        idea.id = 44
        idea.status = "selected"

        http_client = Mock()
        http_client_class.return_value.__enter__.return_value = http_client

        cn_offer = Mock()
        cn_offer.supplier.name = "CJdropshipping"

        cj_searcher = Mock()
        cj_searcher.supplier.name = "CJdropshipping"
        cj_searcher.search_for_idea.return_value = []
        cj_searcher.search_for_idea_in_country.return_value = [cn_offer]

        factory_build.return_value = [cj_searcher]
        visual_factory_build.return_value = Mock()

        summary = SupplierCandidateCollectionRunner.collect(
            product_idea=idea,
        )

        cj_searcher.search_for_idea_in_country.assert_called_once_with(
            product_idea=idea,
            country_code="CN",
        )
        self.assertEqual(summary["offers_found"], 1)
