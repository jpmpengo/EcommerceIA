from decimal import Decimal
from uuid import uuid4

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
        activate=True,
    ):
        saved_prices = []
        batch_id = uuid4()

        if activate:
            ComparablePrice.objects.filter(
                supplier_offer=supplier_offer,
                is_current=True,
            ).update(is_current=False)

        for result in results[
            :cls.MAXIMUM_COMPARABLE_PRICES
        ]:
            source_url = result[
                "source_url"
            ]

            comparable_price = (
                ComparablePrice.objects
                .create(
                    supplier_offer=(
                        supplier_offer
                    ),
                    source_url=source_url,
                    image_url=result.get("image_url") or "",
                    shipping_days_min=result.get("shipping_days_min"),
                    shipping_days_max=result.get("shipping_days_max"),
                    shipping_cost=Decimal(str(result["shipping_cost"])) if result.get("shipping_cost") is not None else None,
                    shipping_currency=result.get("shipping_currency"),
                    free_shipping=result.get("free_shipping"),
                    shipping_destination_country=result.get("shipping_destination_country"),
                    shipping_evidence=result.get("shipping_evidence"),
                    product_name=result["product_name"],
                    observed_price=Decimal(
                        str(result["observed_price"])
                    ),
                    currency=result["currency"],
                    source_title=result["source_title"],
                    search_query=search_query,
                    evidence=result["evidence"],
                    model_name=model_name,
                    commercial_segment=result.get('commercial_segment') or 'unclassified',
                    commercial_segment_reason=result.get('commercial_segment_reason') or None,
                    collection_batch_id=batch_id,
                    is_current=activate,
                )
            )

            saved_prices.append(
                comparable_price
            )

        return saved_prices
