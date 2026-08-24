import csv
import unicodedata
from pathlib import Path

from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)


class WooCommerceLocalCollector(
    BaseMarketCollector
):

    source_name = "woocommerce_local"

    def __init__(
        self,
        csv_path,
        currency="EUR",
    ):
        self.csv_path = Path(csv_path)
        self.currency = currency

    def collect(
        self,
        query,
    ):
        normalized_query = self._normalize_text(
            query
        )

        query_terms = normalized_query.split()

        results = []

        with self.csv_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(
                csv_file
            )

            for row in reader:
                searchable_text = (
                    f"{row.get('Name', '')} "
                    f"{row.get('Description', '')}"
                )

                normalized_text = (
                    self._normalize_text(
                        searchable_text
                    )
                )

                if not all(
                    term in normalized_text
                    for term in query_terms
                ):
                    continue

                external_id = (
                    row.get("SKU", "").strip()
                    or row.get("ID", "").strip()
                )

                images = (
                    row.get("Images", "")
                    .strip()
                )

                image_url = (
                    images.split(",", 1)[0].strip()
                    if images
                    else ""
                )

                results.append(
                    {
                        "source": self.source_name,
                        "external_id": external_id,
                        "name": (
                            row.get("Name", "")
                            .strip()
                        ),
                        "description": (
                            row.get(
                                "Description",
                                "",
                            )
                            .strip()
                        ),
                        "observed_price": (
                            row.get(
                                "Regular price",
                                "",
                            )
                            .strip()
                            or None
                        ),
                        "currency": self.currency,
                        "product_url": "",
                        "image_url": image_url,
                        "raw_data": {
                            "query": query,
                            "woocommerce_id": (
                                row.get("ID", "")
                                .strip()
                            ),
                        },
                    }
                )

        self.validate_results(
            results
        )

        return results

    @staticmethod
    def _normalize_text(
        value,
    ):
        normalized = unicodedata.normalize(
            "NFKD",
            value,
        )

        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        ).casefold()