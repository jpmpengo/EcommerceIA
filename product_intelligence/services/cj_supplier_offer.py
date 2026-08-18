from decimal import Decimal

from product_intelligence.models import SupplierOffer


class CJSupplierOfferService:

    def create_offer(self, supplier, product):
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
                product.get(
                    "shipping_cost",
                    "0.00",
                )
            ),
            currency=product.get("currency") or "EUR",
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
    ):
        return SupplierOffer.objects.create(
            supplier=supplier,
            supplier_product_id=(
                variant.get("vid")
                or variant.get("pid")
                or product.get("external_id")
                or ""
            ),
            product_name=(
                variant.get("variantNameEn")
                or product["name"]
            ),
            purchase_price=Decimal(
                str(variant["variantSellPrice"])
            ),
            shipping_cost=Decimal("0.00"),
            currency=product.get("currency") or "USD",
            stock=stock,
            product_url=product.get(
                "product_url",
                "",
            ),
            image_url=product.get(
                "image_url",
                "",
            ),
        )

        

        