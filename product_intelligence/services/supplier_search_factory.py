from product_intelligence.models import (
    Supplier,
)
from product_intelligence.services.cj_auth_client import (
    CJAuthClient,
)
from product_intelligence.services.cj_client import (
    CJClient,
)
from product_intelligence.services.cj_supplier_offer import (
    CJSupplierOfferService,
)
from product_intelligence.services.cj_supplier_searcher import (
    CJSupplierSearcher,
)
from product_intelligence.services.printful_client import (
    PrintfulClient,
)
from product_intelligence.services.printful_supplier_offer import (
    PrintfulSupplierOfferService,
)
from product_intelligence.services.printful_supplier_searcher import (
    PrintfulSupplierSearcher,
)
from product_intelligence.services.supplier_product_matching import (
    SupplierProductMatchingService,
)
from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)


class SupplierSearchFactory:

    MAX_OFFERS_PER_SUPPLIER = 5

    @classmethod
    def build(
        cls,
        http_client,
        cj_api_key=None,
        printful_api_token=None,
    ):
        searchers = []

        if cj_api_key:
            searchers.append(
                cls._build_cj_searcher(
                    http_client=http_client,
                    api_key=cj_api_key,
                )
            )

        if printful_api_token:
            searchers.append(
                cls._build_printful_searcher(
                    http_client=http_client,
                    api_token=(
                        printful_api_token
                    ),
                )
            )

        return searchers

    @classmethod
    def _build_cj_searcher(
        cls,
        http_client,
        api_key,
    ):
        supplier, _ = (
            Supplier.objects.get_or_create(
                name="CJdropshipping",
                defaults={
                    "country": "CN",
                    "website": (
                        "https://cjdropshipping.com"
                    ),
                    "supplier_type": (
                        "dropshipper"
                    ),
                },
            )
        )

        access_token = (
            CJAuthClient(
                api_key=api_key,
                http_client=http_client,
            )
            .get_access_token()
        )

        client = CJClient(
            access_token=access_token,
            http_client=http_client,
        )

        offer_service = (
            CJSupplierOfferService(
                variant_features_service=(
                    VariantFeaturesService()
                ),
            )
        )

        return CJSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            max_offers=(
                cls.MAX_OFFERS_PER_SUPPLIER
            ),
        )

    @classmethod
    def _build_printful_searcher(
        cls,
        http_client,
        api_token,
    ):
        supplier, _ = (
            Supplier.objects.get_or_create(
                name="Printful",
                defaults={
                    "country": "US",
                    "website": (
                        "https://www.printful.com"
                    ),
                    "supplier_type": (
                        "print_on_demand"
                    ),
                },
            )
        )

        client = PrintfulClient(
            api_token=api_token,
            http_client=http_client,
        )

        offer_service = (
            PrintfulSupplierOfferService(
                variant_features_service=(
                    VariantFeaturesService()
                ),
            )
        )

        return PrintfulSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=(
                SupplierProductMatchingService()
            ),
            max_offers=(
                cls.MAX_OFFERS_PER_SUPPLIER
            ),
        )