from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from product_intelligence.services.collectors.woocommerce_local import (
    WooCommerceLocalCollector,
)


class WooCommerceLocalCollectorTests(SimpleTestCase):

    def test_collect_returns_matching_normalized_products(
        self,
    ):
        with TemporaryDirectory() as directory:
            csv_path = (
                Path(directory)
                / "woocommerce-products.csv"
            )

            csv_path.write_text(
                (
                    "ID,SKU,Name,Description,"
                    "Regular price,Images\n"
                    "10,RANG-001,"
                    "Organisateur sous évier,"
                    "Rangement modulable,"
                    "29.90,"
                    "https://example.com/rangement.jpg\n"
                    "11,LAMP-001,"
                    "Lampe de bureau,"
                    "Lampe réglable,"
                    "39.90,"
                    "https://example.com/lampe.jpg\n"
                ),
                encoding="utf-8",
            )

            collector = WooCommerceLocalCollector(
                csv_path=csv_path,
            )

            results = collector.collect(
                query="organisateur sous évier",
            )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0],
            {
                "source": "woocommerce_local",
                "external_id": "RANG-001",
                "name": "Organisateur sous évier",
                "description": "Rangement modulable",
                "observed_price": "29.90",
                "currency": "EUR",
                "product_url": "",
                "image_url": (
                    "https://example.com/"
                    "rangement.jpg"
                ),
                "raw_data": {
                    "query": "organisateur sous évier",
                    "woocommerce_id": "10",
                },
            },
        )