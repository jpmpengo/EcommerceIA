from decimal import Decimal

from product_intelligence.models import (
    SupplierOffer,
)


class PrintfulSupplierOfferService:

    def __init__(
        self,
        variant_features_service=None,
    ):
        self.variant_features_service = (
            variant_features_service
        )

    def create_offer_from_variant(
        self,
        supplier,
        product,
        variant,
        market_observation=None,
    ):
        variant_features = {}

        if self.variant_features_service is not None:
            extracted_features = (
                self.variant_features_service.extract(
                    variant=variant,
                )
            )

            variant_features = {
                key: (
                    list(value)
                    if isinstance(value, tuple)
                    else value
                )
                for key, value
                in extracted_features.items()
                if value is not None
            }

        variant_id = str(
            variant["id"]
        )

        lookup = {
            "supplier": supplier,
            "supplier_product_id": variant_id,
        }

        if market_observation is not None:
            lookup["market_observation"] = (
                market_observation
            )

        offer, _ = (
            SupplierOffer.objects.update_or_create(
                **lookup,
                defaults={
                    "product_name": (
                        variant.get("name")
                        or product["title"]
                    ),
                    "purchase_price": Decimal(
                        str(variant["price"])
                    ),
                    "shipping_cost": Decimal(
                        "0.00"
                    ),
                    "currency": (
                        product.get("currency")
                        or "USD"
                    ),
                    "stock": None,
                    "is_available": (
                        variant.get("in_stock")
                    ),
                    "product_url": "",
                    "image_url": (
                        variant.get("image")
                        or product.get("image")
                        or ""
                    ),
                    "variant_features": (
                        variant_features
                    ),
                },
            )
        )

        return offer
