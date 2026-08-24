import httpx

from django.conf import settings

from product_intelligence.services.collectors.etsy import (
    EtsyMarketCollector,
)
from product_intelligence.services.etsy_client import (
    EtsyClient,
)


class MarketplaceCollectorFactory:

    @staticmethod
    def build(
        marketplaces,
    ):
        collectors = {}

        for marketplace in marketplaces:
            if marketplace == "etsy":
                collectors[marketplace] = (
                    MarketplaceCollectorFactory
                    ._build_etsy_collector()
                )
                continue

            raise ValueError(
                (
                    "Aucun collecteur configuré "
                    f"pour {marketplace}."
                )
            )

        return collectors

    @staticmethod
    def _build_etsy_collector():
        api_key = getattr(
            settings,
            "ETSY_API_KEY",
            "",
        )

        shared_secret = getattr(
            settings,
            "ETSY_SHARED_SECRET",
            "",
        )

        if not api_key or not shared_secret:
            raise ValueError(
                (
                    "La configuration Etsy "
                    "est incomplète."
                )
            )

        http_client = httpx.Client(
            timeout=30.0,
        )

        client = EtsyClient(
            api_key=api_key,
            shared_secret=shared_secret,
            http_client=http_client,
        )

        return EtsyMarketCollector(
            client=client,
        )