import ssl

import httpx
import truststore
from openai import OpenAI

from product_intelligence.services.openai_visual_matching_client import (
    OpenAIVisualMatchingClient,
)
from product_intelligence.services.product_visual_matching import (
    ProductVisualMatchingService,
)


class ProductVisualMatchingFactory:

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
            timeout=120.0,
        )

        sdk_client = OpenAI(
            http_client=http_client,
        )

        visual_client = OpenAIVisualMatchingClient(
            client=sdk_client,
            model=selected_model,
        )

        return ProductVisualMatchingService(
            client=visual_client,
        )
