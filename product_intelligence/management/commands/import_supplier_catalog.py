import os
import ssl

import httpx
import truststore

from django.core.management.base import (
    BaseCommand,
)

from product_intelligence.models import (
    Supplier,
)

from product_intelligence.services.cj_auth_client import (
    CJAuthClient,
)

from product_intelligence.services.cj_catalog_importer import (
    CJCatalogImporter,
)

from product_intelligence.services.cj_client import (
    CJClient,
)

from product_intelligence.services.printful_catalog_importer import (
    PrintfulCatalogImporter,
)

from product_intelligence.services.printful_client import (
    PrintfulClient,
)

from product_intelligence.services.supplier_catalog_import import (
    SupplierCatalogImportService,
)


class Command(BaseCommand):

    help = "Import supplier catalog offers."

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--keyword",
            default="mouse pad",
        )

        parser.add_argument(
            "--max-offers",
            type=int,
            default=3,
        )

    def handle(
        self,
        *args,
        **options,
    ):
        keyword = options[
            "keyword"
        ]

        max_offers = options[
            "max_offers"
        ]

        http_client = httpx.Client(
            verify=truststore.SSLContext(
                ssl.PROTOCOL_TLS_CLIENT
            ),
            timeout=30.0,
        )

        try:
            cj_supplier, _ = (
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

            printful_supplier, _ = (
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

            cj_api_key = os.getenv(
                "CJ_API_KEY"
            )

            printful_api_token = os.getenv(
                "PRINTFUL_API_TOKEN"
            )

            if not cj_api_key:
                raise ValueError(
                    "CJ_API_KEY is missing."
                )

            if not printful_api_token:
                raise ValueError(
                    "PRINTFUL_API_TOKEN is missing."
                )

            cj_access_token = (
                CJAuthClient(
                    api_key=cj_api_key,
                    http_client=http_client,
                )
                .get_access_token()
            )

            cj_client = CJClient(
                access_token=cj_access_token,
                http_client=http_client,
            )

            printful_client = PrintfulClient(
                api_token=printful_api_token,
                http_client=http_client,
            )

            cj_importer = CJCatalogImporter(
                client=cj_client,
                supplier=cj_supplier,
                keyword=keyword,
                max_offers=max_offers,
            )

            printful_importer = (
                PrintfulCatalogImporter(
                    client=printful_client,
                    supplier=printful_supplier,
                    max_offers=max_offers,
                )
            )

            service = (
                SupplierCatalogImportService(
                    importers=[
                        cj_importer,
                        printful_importer,
                    ]
                )
            )

            offers = service.import_catalog()

            self.stdout.write(
                f"{len(offers)} supplier offers imported"
            )

        finally:
            http_client.close()
