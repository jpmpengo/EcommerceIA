class SupplierOfferShippingService:

    def __init__(
        self,
        estimation_service,
    ):
        self.estimation_service = (
            estimation_service
        )

    def enrich(
        self,
        supplier_offer,
        destination_country,
        quantity=1,
    ):
        quote = (
            self.estimation_service.estimate(
                offer=supplier_offer,
                destination_country=(
                    destination_country
                ),
                quantity=quantity,
            )
        )

        if quote is None:
            return {
                "status": "unavailable",
                "reason": (
                    "Aucun devis de livraison "
                    "disponible."
                ),
            }

        quote_currency = (
            quote.get("currency")
            or supplier_offer.currency
        )

        if (
            quote_currency
            != supplier_offer.currency
        ):
            return {
                "status": "currency_mismatch",
                "reason": (
                    "La devise du devis de "
                    "livraison ne correspond pas "
                    "à celle de l’offre."
                ),
            }

        shipping_country = (
            quote.get("shipping_country")
            or destination_country
        )

        supplier_offer.shipping_cost = (
            quote.get("cost")
        )

        supplier_offer.shipping_days = (
            quote.get("shipping_days")
        )

        supplier_offer.shipping_country = (
            shipping_country
        )

        supplier_offer.shipping_method = (
            quote.get("method")
            or ""
        )

        supplier_offer.customs_included = (
            quote.get("customs_included")
        )

        supplier_offer.save(
            update_fields=[
                "shipping_cost",
                "shipping_days",
                "shipping_country",
                "shipping_method",
                "customs_included",
            ]
        )

        return {
            "status": "estimated",
            "cost": (
                supplier_offer.shipping_cost
            ),
            "currency": quote_currency,
            "shipping_days": (
                supplier_offer.shipping_days
            ),
            "shipping_country": (
                supplier_offer.shipping_country
            ),
            "method": (
                supplier_offer.shipping_method
            ),
            "customs_included": (
                supplier_offer.customs_included
            ),
        }
