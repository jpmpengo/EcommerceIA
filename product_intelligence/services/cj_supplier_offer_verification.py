class CJSupplierOfferVerificationService:

    def __init__(self, client):
        self.client = client

    def verify(self, offer):
        variant = self.client.get_variant_by_id(
            offer.supplier_product_id
        )

        if not variant:
            offer.is_available = False
            offer.save(update_fields=["is_available"])
            return {
                "status": "unavailable",
                "reason": "La variante CJ n est plus disponible.",
            }

        stock_kwargs = {
            "variant_id": offer.supplier_product_id,
        }
        if offer.stock_country:
            stock_kwargs["country_code"] = offer.stock_country

        stock = self.client.get_variant_stock(**stock_kwargs)

        offer.is_available = (
            stock is not None and stock > 0
        )
        if stock is not None:
            offer.stock = stock

        offer.save(
            update_fields=[
                "is_available",
                "stock",
            ]
        )

        return {
            "status": (
                "available"
                if offer.is_available
                else "unavailable"
            ),
            "variant": variant,
            "stock": stock,
        }
