from decimal import Decimal


class AWShippingEstimator:

    @staticmethod
    def can_handle(offer):
        supplier_name = (
            getattr(
                getattr(offer, "supplier", None),
                "name",
                "",
            )
            or ""
        )
        return supplier_name.lower() == "aw dropship"

    def estimate(
        self,
        offer,
        destination_country,
        quantity=1,
    ):
        if str(destination_country).upper() != "FR":
            return None

        weight = getattr(
            offer,
            "shipping_weight_grams",
            None,
        )

        if weight is None or weight <= 0:
            return None

        total_weight = weight * quantity

        if total_weight <= 250:
            return {
                "cost": Decimal("7.50"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            }

        if total_weight <= 2000:
            return {
                "cost": Decimal("7.80"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            }

        if total_weight <= 5000:
            return {
                "cost": Decimal("12.90"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            }

        if total_weight <= 30000:
            return {
                "cost": Decimal("13.20"),
                "currency": "EUR",
                "shipping_days": 6,
                "shipping_country": "FR",
                "method": "AW Standard",
            }

        return None
