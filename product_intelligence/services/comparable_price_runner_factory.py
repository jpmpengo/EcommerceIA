import ssl

import httpx
import truststore
from openai import OpenAI

from product_intelligence.services.comparable_price_collection import (
    ComparablePriceCollectionService,
)
from product_intelligence.services.comparable_price_collection_runner import (
    ComparablePriceCollectionRunner,
)
from product_intelligence.services.comparable_price_search import (
    ComparablePriceSearchService,
)
from product_intelligence.services.openai_client import (
    OpenAIClient,
)


class ComparablePriceRunnerFactory:

    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def build(
        cls,
        model=None,
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
            timeout=60.0,
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

        return ComparablePriceCollectionRunner(
            collection_service=(
                collection_service
            ),
        )