import os
import ssl

import httpx
import truststore
from openai import OpenAI

from product_intelligence.services.cj_economic_fallback import (
    CJEconomicFallbackService,
)
from product_intelligence.services.comparable_price_collection import (
    ComparablePriceCollectionService,
)
from product_intelligence.services.comparable_price_commercial_classification import (
    ComparablePriceCommercialClassificationService,
)
from product_intelligence.services.comparable_price_collection_runner import (
    ComparablePriceCollectionRunner,
)
from product_intelligence.services.comparable_price_search import (
    ComparablePriceSearchService,
)
from product_intelligence.services.comparable_price_qualification import (
    ComparablePriceQualificationService,
)
from product_intelligence.services.openai_client import (
    OpenAIClient,
)
from product_intelligence.services.product_visual_matching_factory import (
    ProductVisualMatchingFactory,
)
from product_intelligence.services.supplier_offer_visual_matching import (
    SupplierOfferVisualMatchingService,
)
from product_intelligence.services.supplier_delivery_policy import (
    SupplierDeliveryPolicyService,
)
from product_intelligence.services.supplier_offer_research_pipeline import (
    SupplierOfferResearchPipeline,
)
from product_intelligence.services.supplier_offer_shipping import (
    SupplierOfferShippingService,
)
from product_intelligence.services.supplier_shipping_factory import (
    SupplierShippingFactory,
)
from product_intelligence.services.supplier_search_factory import (
    SupplierSearchFactory,
)


class ComparablePriceRunnerFactory:

    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def build_economic_fallback(
        cls,
        model=None,
        destination_country="FR",
    ):
        runner = cls.build(
            model=model,
            destination_country=destination_country,
        )

        cj_api_key = os.getenv(
            "CJ_API_KEY",
            "",
        )

        if not cj_api_key:
            return None

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )
        http_client = httpx.Client(
            verify=ssl_context,
            timeout=60.0,
        )
        cj_searcher = SupplierSearchFactory._build_cj_searcher(
            http_client=http_client,
            api_key=cj_api_key,
        )

        return CJEconomicFallbackService(
            cj_searcher=cj_searcher,
            research_pipeline=(
                runner.research_pipeline
            ),
            qualification_service=(
                runner.qualification_service
            ),
            destination_country=(
                runner.destination_country
            ),
            visual_matching_service=(
                SupplierOfferVisualMatchingService(
                    matching_service=(
                        ProductVisualMatchingFactory.build(
                            model=model,
                        )
                    )
                )
            ),
        )

    @classmethod
    def build(
        cls,
        model=None,
        destination_country="FR",
    ):
        selected_model = (
            model
            or cls.DEFAULT_MODEL
        )

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        http_client = httpx.Client(
            verify=ssl_context,
            timeout=180.0,
        )

        sdk_client = OpenAI(
            http_client=http_client,
        )

        openai_client = OpenAIClient(
            client=sdk_client,
            model=selected_model,
        )

        search_service = (
            ComparablePriceSearchService(
                client=openai_client,
            )
        )

        collection_service = (
            ComparablePriceCollectionService(
                search_service=search_service,
                model_name=selected_model,
            )
        )

        delivery_policy = (
            SupplierDeliveryPolicyService()
        )

        cj_api_key = os.getenv(
            "CJ_API_KEY",
            "",
        )

        shipping_estimation_service = (
            SupplierShippingFactory.build(
                http_client=http_client,
                aw_api_token=os.getenv(
                    "AW_API_TOKEN",
                    "",
                ),
                cj_api_key=cj_api_key,
                printful_api_token=os.getenv(
                    "PRINTFUL_API_TOKEN",
                    "",
                ),
                eprolo_api_key=os.getenv(
                    "EPROLO_API_KEY",
                    "",
                ),
                eprolo_api_secret=os.getenv(
                    "EPROLO_API_SECRET",
                    "",
                ),
                eprolo_api_base_url=os.getenv(
                    "EPROLO_API_BASE_URL",
                    "",
                ) or None,
                maximum_shipping_days=(
                    delivery_policy
                    .absolute_maximum_days
                ),
            )
        )

        shipping_service = (
            SupplierOfferShippingService(
                estimation_service=(
                    shipping_estimation_service
                ),
            )
        )

        research_pipeline = (
            SupplierOfferResearchPipeline(
                shipping_service=shipping_service,
                delivery_policy=delivery_policy,
                comparable_price_collection=(
                    collection_service
                ),
            )
        )

        return ComparablePriceCollectionRunner(
            research_pipeline=(
                research_pipeline
            ),
            qualification_service=(
                ComparablePriceQualificationService
            ),
            commercial_classification_service=(
                ComparablePriceCommercialClassificationService(
                    client=openai_client,
                )
            ),
            destination_country=(
                destination_country
            ),
        )
