import ssl

import httpx
import truststore
from openai import OpenAI

from product_intelligence.services.openai_client import OpenAIClient
from product_intelligence.services.product_idea_visual_reference_search import ProductIdeaVisualReferenceSearchService
from product_intelligence.services.product_idea_visual_reference_collection import ProductIdeaVisualReferenceCollectionService


class ProductIdeaVisualReferenceCollectionRunner:

    DEFAULT_MODEL = "gpt-5.6-luna"

    @classmethod
    def collect(cls, product_idea, model=None):
        selected_model = model or cls.DEFAULT_MODEL

        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        http_client = httpx.Client(
            verify=ssl_context,
            timeout=120.0,
        )

        sdk_client = OpenAI(
            http_client=http_client,
        )

        client = OpenAIClient(
            client=sdk_client,
            model=selected_model,
        )

        search_service = ProductIdeaVisualReferenceSearchService(
            client=client,
        )

        collection_service = ProductIdeaVisualReferenceCollectionService(
            search_service=search_service,
            model_name=selected_model,
        )

        return collection_service.collect(
            product_idea=product_idea,
        )
