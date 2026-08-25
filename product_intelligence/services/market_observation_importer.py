from decimal import Decimal

from product_intelligence.models import (
    MarketObservation,
    MarketObservationSnapshot,
)


class MarketObservationImporter:

    def __init__(
        self,
        collector,
    ):
        self.collector = collector

    def import_query(
        self,
        query,
        max_results=None,
    ):
        results = self.collector.collect(
            query=query
        )

        if max_results is not None:
            results = list(
                results
            )[
                :max_results
            ]

        self.collector.validate_results(
            results
        )

        imported = []

        for data in results:
            observation, created = (
                MarketObservation.objects.update_or_create(
                    source=data["source"],
                    external_id=data["external_id"],
                    defaults={
                        "name": data["name"],
                        "description": data.get(
                            "description",
                            "",
                        ),
                        "observed_price": (
                            Decimal(
                                str(
                                    data["observed_price"]
                                )
                            )
                            if data.get(
                                "observed_price"
                            )
                            is not None
                            else None
                        ),
                        "currency": data.get(
                            "currency",
                            "EUR",
                        ),
                        "product_url": data.get(
                            "product_url",
                            "",
                        ),
                        "image_url": data.get(
                            "image_url",
                            "",
                        ),
                        "raw_data": data.get(
                            "raw_data",
                            {},
                        ),
                    },
                )
            )

            MarketObservationSnapshot.objects.create(
                observation=observation,
                observed_price=(
                    Decimal(
                        str(
                            data["observed_price"]
                        )
                    )
                    if data.get(
                        "observed_price"
                    )
                    is not None
                    else None
                ),
                currency=data.get(
                    "currency",
                    "EUR",
                ),
                raw_data=data.get(
                    "raw_data",
                    {},
                ),
            )

            imported.append(
                {
                    "observation": observation,
                    "created": created,
                }
            )

        return imported
