from decimal import Decimal

from product_intelligence.models import (
    SupplierOffer,
)


class CJSupplierOfferService:

    def __init__(
        self,
        variant_features_service=None,
    ):
        self.variant_features_service = (
            variant_features_service
        )

    def create_offer(
        self,
        supplier,
        product,
    ):
        return SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id=product.get(
                "external_id",
                "",
            ),
            product_name=product["name"],
            purchase_price=Decimal(
                str(product["purchase_price"])
            ),
            shipping_cost=Decimal(
                str(
                    product.get(
                        "shipping_cost",
                        "0.00",
                    )
                )
            ),
            currency=(
                product.get("currency")
                or "EUR"
            ),
            stock=product.get("stock"),
            product_url=product.get(
                "product_url",
                "",
            ),
            image_url=product.get(
                "image_url",
                "",
            ),
        )

    def create_offer_from_variant(
        self,
        supplier,
        product,
        variant,
        stock,
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

        variant_id = (
            variant.get("vid")
            or variant.get("pid")
            or product.get("external_id")
            or ""
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
                        variant.get(
                            "variantNameEn"
                        )
                        or product["name"]
                    ),
                    "purchase_price": Decimal(
                        str(
                            variant[
                                "variantSellPrice"
                            ]
                        )
                    ),
                    "shipping_cost": Decimal(
                        "0.00"
                    ),
                    "currency": (
                        product.get("currency")
                        or "USD"
                    ),
                    "stock": stock,
                    "product_url": product.get(
                        "product_url",
                        "",
                    ),
                    "image_url": (
                        variant.get(
                            "variantImage"
                        )
                        or product.get(
                            "image_url",
                            "",
                        )
                    ),
                    "variant_features": (
                        variant_features
                    ),
                },
            )
        )

        return offer
