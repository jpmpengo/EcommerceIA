import os
from unittest.mock import (
    Mock,
    patch,
)

from django.test import SimpleTestCase

from product_intelligence.services.supplier_candidate_collection_runner import (
    SupplierCandidateCollectionRunner,
)


class SupplierCandidateCollectionRunnerTests(
    SimpleTestCase
):

    @patch.dict(
        os.environ,
        {
            "CJ_API_KEY": "cj-api-key",
            "PRINTFUL_API_TOKEN": "",
        },
        clear=True,
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
        )

        self.assertEqual(
            summary,
            {
                "product_idea_id": 42,
                "suppliers_searched": 1,
                "offers_found": 0,
                "offers_by_supplier": {},
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