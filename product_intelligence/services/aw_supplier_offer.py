from decimal import Decimal

from product_intelligence.models import SupplierOffer
from product_intelligence.services.product_comparability_attributes import ProductComparabilityAttributesService


class AWSupplierOfferService:

    def create_offer(
        self,
        supplier,
        product,
        market_observation=None,
        product_idea=None,
        supplier_search_keyword="",
    ):
        stock = product.get("current_stock")
        image = product.get("image") or {}
        variant_features = ProductComparabilityAttributesService().extract(
            name=product.get("name") or "",
            evidence=product.get("description") or "",
        )

        offer, unused_created = SupplierOffer.objects.update_or_create(
            supplier=supplier,
            product_idea=product_idea,
            supplier_product_id=str(product.get("id") or ""),
            defaults={
                "market_observation": market_observation,
                "supplier_sku": product.get("code") or "",
                "supplier_search_keyword": supplier_search_keyword,
                "product_name": product["name"],
                "purchase_price": Decimal(str(product["price"])),
                "currency": product.get("currency_code") or "EUR",
                "stock": stock,
                "shipping_weight_grams": product.get("gross_weight"),
                "stock_country": "",
                "is_available": (stock > 0 if stock is not None else None),
                "image_url": image.get("original") or "",
                "variant_features": variant_features,
            },
        )
        return offer
