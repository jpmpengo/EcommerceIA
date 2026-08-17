
from decimal import Decimal

from product_intelligence.models import (
    SupplierOffer,
)


class PrintfulSupplierOfferService:

    def create_offer_from_variant(
        self,
        supplier,
        product,
        variant,
    ):
        return SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id=str(
                variant["id"]
            ),
            product_name=(
                variant.get("name")
                or product["title"]
            ),
            purchase_price=Decimal(
                str(variant["price"])
            ),
            shipping_cost=Decimal(
                "0.00"
            ),
            currency=(
                product.get("currency")
                or "USD"
            ),
            stock=None,
            is_available=variant.get(
                "in_stock"
            ),
            product_url="",
            image_url=(
                variant.get("image")
                or product.get("image")
                or ""
            ),
        )

        