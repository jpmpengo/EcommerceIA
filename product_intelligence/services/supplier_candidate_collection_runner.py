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
from product_intelligence.services.product_visual_matching_factory import (
    ProductVisualMatchingFactory,
)
from product_intelligence.services.supplier_offer_visual_matching import (
    SupplierOfferVisualMatchingService,
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

        aw_api_token = os.getenv(
            "AW_API_TOKEN",
            "",
        )

        eprolo_api_key = os.getenv(
            "EPROLO_API_KEY",
            "",
        )
        eprolo_api_secret = os.getenv(
            "EPROLO_API_SECRET",
            "",
        )

        if (
            not cj_api_key
            and not printful_api_token
            and not aw_api_token
            and not (
                eprolo_api_key
                and eprolo_api_secret
            )
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
                    aw_api_token=aw_api_token,
                    aw_api_base_url=os.getenv(
                        "AW_API_BASE_URL",
                        "",
                    ) or None,
                    eprolo_api_key=eprolo_api_key,
                    eprolo_api_secret=(
                        eprolo_api_secret
                    ),
                    eprolo_api_base_url=os.getenv(
                        "EPROLO_API_BASE_URL",
                        "",
                    ) or None,
                    eprolo_max_catalog_pages=int(
                        os.getenv(
                            "EPROLO_MAX_CATALOG_PAGES",
                            "5",
                        )
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

            product_visual_matching = (
                ProductVisualMatchingFactory.build()
            )

            from product_intelligence.services.product_idea_visual_reference_collection_runner import ProductIdeaVisualReferenceCollectionRunner

            visual_matching_service = (
                SupplierOfferVisualMatchingService(
                    matching_service=(
                        product_visual_matching
                    ),
                    reference_collector=ProductIdeaVisualReferenceCollectionRunner.collect,
                )
            )

            collection_service = (
                SupplierCandidateCollectionService(
                    search_service=(
                        search_service
                    ),
                    visual_matching_service=(
                        visual_matching_service
                    ),
                )
            )

            return collection_service.collect(
                product_idea=product_idea,
            )
