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
        maximum_shipping_days=20,
    ):
        self.client = client
        self.origin_country = (
            origin_country
        )
        self.maximum_shipping_days = (
            maximum_shipping_days
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
        stock_country = getattr(offer, "stock_country", "")
        origin_country = (
            stock_country.strip()
            if isinstance(stock_country, str) and stock_country.strip()
            else self.origin_country
        )

        options = (
            self.client.calculate_freight(
                variant_id=(
                    offer.supplier_product_id
                ),
                origin_country=(
                    origin_country
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
            if getattr(offer, "free_shipping", None) is True:
                shipping_days = None
                method = "Free shipping included"
                parent_product_id = getattr(
                    offer,
                    "supplier_parent_product_id",
                    "",
                )
                weight = getattr(
                    offer,
                    "shipping_weight_grams",
                    None,
                )

                if parent_product_id and weight:
                    product_detail = self.client.get_product_detail(
                        product_id=parent_product_id,
                    )
                    if isinstance(product_detail, dict):
                        product_sku = product_detail.get("productSku")
                        product_properties = product_detail.get(
                            "productProEnSet"
                        ) or []
                        if product_sku and product_properties:
                            tip_options = self.client.calculate_freight_tip(
                                product_sku=product_sku,
                                origin_country=origin_country,
                                destination_country=destination_country,
                                weight=weight,
                                product_properties=product_properties,
                                quantity=quantity,
                            )
                            for tip_option in tip_options:
                                if not isinstance(tip_option, dict):
                                    continue
                                arrival_time = str(
                                    tip_option.get("arrivalTime", "")
                                )
                                day_values = [
                                    int(value)
                                    for value in re.findall(r"\d+", arrival_time)
                                ]
                                if day_values:
                                    shipping_days = max(day_values)
                                    method = (
                                        tip_option.get("logisticName")
                                        or method
                                    )
                                    break

                return {
                    "cost": Decimal("0"),
                    "currency": "USD",
                    "shipping_days": shipping_days,
                    "shipping_country": destination_country,
                    "method": method,
                }
            return None

        parent_product_id = getattr(
            offer,
            "supplier_parent_product_id",
            "",
        )
        weight = getattr(
            offer,
            "shipping_weight_grams",
            None,
        )

        if parent_product_id and weight:
            product_detail = self.client.get_product_detail(
                product_id=parent_product_id,
            )
            if isinstance(product_detail, dict):
                product_sku = product_detail.get("productSku")
                product_properties = product_detail.get("productProEnSet") or []
                if product_sku and product_properties:
                    tip_options = self.client.calculate_freight_tip(
                        product_sku=product_sku,
                        origin_country=origin_country,
                        destination_country=destination_country,
                        weight=weight,
                        product_properties=product_properties,
                        quantity=quantity,
                    )
                    for tip_option in tip_options:
                        if not isinstance(tip_option, dict):
                            continue
                        raw_total = tip_option.get("totalPostageFee")
                        if raw_total is None:
                            raw_total = tip_option.get("discountFee")
                        try:
                            cost = Decimal(str(raw_total))
                        except (InvalidOperation, TypeError, ValueError):
                            continue
                        if cost < 0:
                            continue
                        arrival_time = str(tip_option.get("arrivalTime", ""))
                        day_values = [
                            int(value)
                            for value in re.findall(r"\d+", arrival_time)
                        ]
                        shipping_days = max(day_values) if day_values else None
                        option_data = tip_option.get("option") or {}
                        method = option_data.get("enName") or ""
                        cn_name = option_data.get("cnName") or ""
                        message = str(tip_option.get("message") or "")
                        tariff = tip_option.get("tariff")
                        customs_included = (
                            "包税" in cn_name
                            or (
                                tariff is not None
                                and Decimal(str(tariff or 0)) > 0
                            )
                        ) and "DDU" not in message.upper()
                        valid_quotes.append({
                            "cost": cost,
                            "currency": "USD",
                            "shipping_days": shipping_days,
                            "shipping_country": destination_country,
                            "method": method,
                            "customs_included": customs_included,
                        })

        admissible_quotes = [
            quote
            for quote in valid_quotes
            if (
                quote["shipping_days"]
                is not None
                and quote["shipping_days"]
                <= self.maximum_shipping_days
            )
        ]

        customs_included_quotes = [
            quote
            for quote in admissible_quotes
            if quote.get("customs_included") is True
        ]

        candidate_quotes = (
            customs_included_quotes
            or admissible_quotes
            or valid_quotes
        )

        return min(
            candidate_quotes,
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
