import re

from decimal import (
    Decimal,
    InvalidOperation,
)


class CJShippingEstimator:

    def __init__(
        self,
        client,
        origin_country="CN",
    ):
        self.client = client
        self.origin_country = (
            origin_country
        )

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
            == "cjdropshipping"
        )

    def estimate(
        self,
        offer,
        destination_country,
        quantity=1,
    ):
        options = (
            self.client.calculate_freight(
                variant_id=(
                    offer.supplier_product_id
                ),
                origin_country=(
                    self.origin_country
                ),
                destination_country=(
                    destination_country
                ),
                quantity=quantity,
            )
        )

        valid_quotes = []

        for option in options:
            if not isinstance(
                option,
                dict,
            ):
                continue

            raw_total = option.get(
                "totalPostageFee"
            )

            try:
                if raw_total is not None:
                    cost = Decimal(
                        str(raw_total)
                    )
                else:
                    cost = Decimal(
                        str(
                            option[
                                "logisticPrice"
                            ]
                        )
                    )

                    cost += Decimal(
                        str(
                            option.get(
                                "taxesFee",
                                0,
                            )
                            or 0
                        )
                    )

                    cost += Decimal(
                        str(
                            option.get(
                                "clearanceOperationFee",
                                0,
                            )
                            or 0
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

            aging = str(
                option.get(
                    "logisticAging",
                    "",
                )
            )

            day_values = [
                int(value)
                for value in re.findall(
                    r"\d+",
                    aging,
                )
            ]

            shipping_days = (
                max(day_values)
                if day_values
                else None
            )

            valid_quotes.append(
                {
                    "cost": cost,
                    "currency": "USD",
                    "shipping_days": (
                        shipping_days
                    ),
                    "shipping_country": (
                        destination_country
                    ),
                    "method": (
                        option.get(
                            "logisticName"
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
