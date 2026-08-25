import os
import ssl

import httpx
import truststore

from product_intelligence.services.multi_supplier_search import (
    MultiSupplierSearchService,
)
from product_intelligence.services.supplier_candidate_collection import (
    SupplierCandidateCollectionService,
)
from product_intelligence.services.supplier_search_factory import (
    SupplierSearchFactory,
)


class SupplierCandidateCollectionRunner:

    @classmethod
    def collect(
        cls,
        product_idea,
    ):
        cj_api_key = os.getenv(
            "CJ_API_KEY",
            "",
        )

        printful_api_token = os.getenv(
            "PRINTFUL_API_TOKEN",
            "",
        )

        if (
            not cj_api_key
            and not printful_api_token
        ):
            raise ValueError(
                (
                    "Aucun fournisseur "
                    "n’est configuré."
                )
            )

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        with httpx.Client(
            verify=ssl_context,
            timeout=60.0,
        ) as http_client:
            searchers = (
                SupplierSearchFactory.build(
                    http_client=http_client,
                    cj_api_key=cj_api_key,
                    printful_api_token=(
                        printful_api_token
                    ),
                )
            )

            if not searchers:
                raise ValueError(
                    (
                        "Aucun fournisseur "
                        "n’est configuré."
                    )
                )

            search_service = (
                MultiSupplierSearchService(
                    supplier_searchers=searchers,
                )
            )

            collection_service = (
                SupplierCandidateCollectionService(
                    search_service=(
                        search_service
                    ),
                )
            )

            return collection_service.collect(
                product_idea=product_idea,
            )