import time

from product_intelligence.models import (
    Supplier,
)
from product_intelligence.services.aw_client import (
    AWClient,
)
from product_intelligence.services.aw_supplier_offer import (
    AWSupplierOfferService,
)
from product_intelligence.services.aw_supplier_searcher import (
    AWSupplierSearcher,
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
from product_intelligence.services.eprolo_client import (
    EproloClient,
)
from product_intelligence.services.eprolo_supplier_offer import (
    EproloSupplierOfferService,
)
from product_intelligence.services.eprolo_supplier_searcher import (
    EproloSupplierSearcher,
)
from product_intelligence.services.eprolo_category_resolver import (
    EproloCategoryResolver,
)
from product_intelligence.services.eprolo_product_matching import (
    EproloProductMatchingService,
)
from product_intelligence.services.supplier_category_matching import (
    SupplierCategoryMatchingService,
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
        eprolo_api_key=None,
        eprolo_api_secret=None,
        eprolo_api_base_url=None,
        eprolo_max_catalog_pages=5,
        aw_api_token=None,
        aw_api_base_url=None,
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

        if eprolo_api_key and eprolo_api_secret:
            searchers.append(
                cls._build_eprolo_searcher(
                    http_client=http_client,
                    api_key=eprolo_api_key,
                    api_secret=eprolo_api_secret,
                    base_url=eprolo_api_base_url,
                    max_catalog_pages=(
                        eprolo_max_catalog_pages
                    ),
                )
            )

        if aw_api_token:
            searchers.append(
                cls._build_aw_searcher(
                    http_client=http_client,
                    api_token=aw_api_token,
                    api_base_url=aw_api_base_url,
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
            category_matching_service=(
                SupplierCategoryMatchingService()
            ),
            sleep_func=time.sleep,
            request_delay=1.3,
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

    @classmethod
    def _build_eprolo_searcher(
        cls,
        http_client,
        api_key,
        api_secret,
        base_url=None,
        max_catalog_pages=5,
    ):
        supplier, _ = Supplier.objects.get_or_create(
            name="EPROLO",
            defaults={
                "country": "CN",
                "website": "https://eprolo.com",
                "supplier_type": "dropshipper",
            },
        )
        client = EproloClient(
            api_key=api_key,
            api_secret=api_secret,
            http_client=http_client,
            base_url=base_url,
        )
        offer_service = EproloSupplierOfferService(
            variant_features_service=(
                VariantFeaturesService()
            )
        )
        return EproloSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=offer_service,
            matching_service=EproloProductMatchingService(),
            category_resolver=EproloCategoryResolver(),
            max_offers=cls.MAX_OFFERS_PER_SUPPLIER,
            max_catalog_pages=max_catalog_pages,
        )

    @classmethod
    def _build_aw_searcher(
        cls,
        http_client,
        api_token,
        api_base_url=None,
    ):
        supplier, _ = Supplier.objects.get_or_create(
            name="AW Dropship",
            defaults={
                "country": "SK",
                "website": "https://www.aw-dropship.com",
                "supplier_type": "dropshipper",
            },
        )

        client = AWClient(
            api_token=api_token,
            api_base_url=api_base_url,
            http_client=http_client,
        )

        return AWSupplierSearcher(
            client=client,
            supplier=supplier,
            offer_service=AWSupplierOfferService(),
            matching_service=EproloProductMatchingService(),
            max_offers=cls.MAX_OFFERS_PER_SUPPLIER,
        )

