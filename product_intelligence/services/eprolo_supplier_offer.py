from decimal import Decimal

from product_intelligence.models import SupplierOffer


class EproloSupplierOfferService:

    def __init__(self, variant_features_service=None):
        self.variant_features_service = (
            variant_features_service
        )

    def create_offer_from_variant(
        self,
        supplier,
        product,
        variant,
        market_observation=None,
        product_idea=None,
        supplier_search_keyword="",
    ):
        variant_id = str(variant["id"])
        product_id = str(product["id"])
        product_title = (
            product.get("title")
            or "Produit EPROLO"
        ).strip()
        variant_title = str(
            variant.get("title") or ""
        ).strip()
        if (
            variant_title
            and variant_title.lower()
            not in product_title.lower()
        ):
            offer_name = (
                f"{product_title} - {variant_title}"
            )
        else:
            offer_name = product_title
        features = {}
        if self.variant_features_service is not None:
            normalized_variant = dict(variant)
            normalized_variant["name"] = offer_name
            extracted = (
                self.variant_features_service.extract(
                    normalized_variant
                )
            )
            features = {
                key: list(value)
                if isinstance(value, tuple)
                else value
                for key, value in extracted.items()
                if value is not None
            }

        lookup = {
            "supplier": supplier,
            "supplier_product_id": variant_id,
        }
        if market_observation is not None:
            lookup["market_observation"] = (
                market_observation
            )
        if product_idea is not None:
            lookup["product_idea"] = product_idea

        stock = variant.get("inventory_quantity")
        try:
            stock = int(stock) if stock is not None else None
        except (TypeError, ValueError):
            stock = None

        offer, _ = SupplierOffer.objects.update_or_create(
            **lookup,
            defaults={
                "supplier_parent_product_id": product_id,
                "supplier_sku": variant.get("sku") or "",
                "supplier_search_keyword": supplier_search_keyword,
                "product_name": offer_name,
                "purchase_price": Decimal(
                    str(variant["cost"])
                ),
                "shipping_cost": None,
                "currency": "USD",
                "stock": stock,
                "is_available": (
                    stock is None or stock > 0
                ),
                "product_url": "",
                "image_url": (
                    variant.get("image")
                    or product.get("imagefirst")
                    or ""
                ),
                "variant_features": features,
            },
        )
        return offer
