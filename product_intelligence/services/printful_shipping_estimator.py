from decimal import (
    Decimal,
    InvalidOperation,
)


class PrintfulShippingEstimator:

    def __init__(
        self,
        client,
    ):
        self.client = client

    @staticmethod
    def can_handle(
        offer,
    ):
        supplier_name = (
            getattr(
                getattr(
                    offer,
                    "supplier",
                    None,
                ),
                "name",
                "",
            )
            or ""
        )

        return (
            supplier_name.lower()
            == "printful"
        )

    def estimate(
        self,
        offer,
        destination_country,
        quantity=1,
    ):
        try:
            variant_id = int(
                offer.supplier_product_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        currency = (
            getattr(
                offer,
                "currency",
                None,
            )
            or "USD"
        )

        rates = (
            self.client.get_shipping_rates(
                variant_id=variant_id,
                destination_country=(
                    destination_country
                ),
                quantity=quantity,
                currency=currency,
            )
        )

        standard_rates = [
            rate
            for rate in rates
            if (
                isinstance(
                    rate,
                    dict,
                )
                and str(
                    rate.get(
                        "shipping",
                        "",
                    )
                ).upper()
                == "STANDARD"
            )
        ]

        candidate_rates = (
            standard_rates
            or rates
        )

        valid_quotes = []

        for rate in candidate_rates:
            if not isinstance(
                rate,
                dict,
            ):
                continue

            try:
                cost = Decimal(
                    str(
                        rate["rate"]
                    )
                )
            except (
                InvalidOperation,
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            if cost < 0:
                continue

            shipping_days = (
                rate.get(
                    "max_delivery_days"
                )
            )

            try:
                if shipping_days is not None:
                    shipping_days = int(
                        shipping_days
                    )
            except (
                TypeError,
                ValueError,
            ):
                shipping_days = None

            valid_quotes.append(
                {
                    "cost": cost,
                    "currency": (
                        rate.get(
                            "currency"
                        )
                        or currency
                    ),
                    "shipping_days": (
                        shipping_days
                    ),
                    "shipping_country": (
                        destination_country
                    ),
                    "method": (
                        rate.get(
                            "shipping_method_name"
                        )
                        or rate.get(
                            "shipping"
                        )
                        or ""
                    ),
                }
            )

        if not valid_quotes:
            return None

        return min(
            valid_quotes,
            key=lambda quote: (
                quote["cost"],
                (
                    quote["shipping_days"]
                    if quote[
                        "shipping_days"
                    ] is not None
                    else float("inf")
                ),
            ),
        )
