from decimal import Decimal

from django.db import transaction

from product_intelligence.models import (
    ComparablePrice,
)


class ComparablePricePersistenceService:

    MAXIMUM_COMPARABLE_PRICES = 5

    @classmethod
    @transaction.atomic
    def save(
        cls,
        supplier_offer,
        results,
        search_query,
        model_name,
    ):
        saved_prices = []

        for result in results[
            :cls.MAXIMUM_COMPARABLE_PRICES
        ]:
            source_url = result[
                "source_url"
            ]

            comparable_price, _ = (
                ComparablePrice.objects
                .update_or_create(
                    supplier_offer=(
                        supplier_offer
                    ),
                    source_url=source_url,
                    defaults={
                        "product_name": (
                            result[
                                "product_name"
                            ]
                        ),
                        "observed_price": (
                            Decimal(
                                str(
                                    result[
                                        "observed_price"
                                    ]
                                )
                            )
                        ),
                        "currency": (
                            result["currency"]
                        ),
                        "source_title": (
                            result[
                                "source_title"
                            ]
                        ),
                        "search_query": (
                            search_query
                        ),
                        "evidence": (
                            result["evidence"]
                        ),
                        "model_name": (
                            model_name
                        ),
                    },
                )
            )

            saved_prices.append(
                comparable_price
            )

        return saved_prices