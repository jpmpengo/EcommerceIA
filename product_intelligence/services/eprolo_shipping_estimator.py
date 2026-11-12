import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


class EproloShippingEstimator:

    def __init__(
        self,
        client,
        maximum_shipping_days=20,
        maximum_rate_age_days=730,
        now_factory=None,
    ):
        self.client = client
        self.maximum_shipping_days = maximum_shipping_days
        self.maximum_rate_age_days = maximum_rate_age_days
        self.now_factory = (
            now_factory
            or (lambda: datetime.now(timezone.utc))
        )

    @staticmethod
    def can_handle(offer):
        name = getattr(
            getattr(offer, "supplier", None),
            "name",
            "",
        )
        return (name or "").lower() == "eprolo"

    def estimate(
        self,
        offer,
        destination_country,
        quantity=1,
    ):
        if not offer.supplier_parent_product_id:
            return None
        rates = self.client.get_shipping_rates(
            product_id=offer.supplier_parent_product_id,
            variant_id=offer.supplier_product_id,
            destination_country=destination_country,
        )
        valid = []
        for rate in rates:
            if not isinstance(rate, dict):
                continue
            try:
                cost = Decimal(str(rate["cost"])) * quantity
            except (
                InvalidOperation,
                KeyError,
                TypeError,
                ValueError,
            ):
                continue
            if cost < 0:
                continue
            days = [
                int(value)
                for value in re.findall(
                    r"\d+",
                    str(rate.get("shiptime") or ""),
                )
            ]
            shipping_days = max(days) if days else None
            if shipping_days is None:
                continue

            updated_at = self._parse_updated_at(
                rate.get("updatetime")
            )
            if (
                updated_at is not None
                and (
                    self.now_factory() - updated_at
                ).days > self.maximum_rate_age_days
            ):
                continue

            valid.append(
                {
                    "cost": cost,
                    "currency": "USD",
                    "shipping_days": shipping_days,
                    "shipping_country": (
                        destination_country.upper()
                    ),
                    "method": (
                        rate.get("ship_method") or ""
                    ),
                }
            )
        if not valid:
            return None
        admissible = [
            quote for quote in valid
            if quote["shipping_days"]
            <= self.maximum_shipping_days
        ]
        candidates = admissible or valid
        return min(
            candidates,
            key=lambda quote: (
                quote["cost"],
                quote["shipping_days"],
            ),
        )

    @staticmethod
    def _parse_updated_at(value):
        if not value:
            return None
        try:
            return datetime.strptime(
                str(value),
                "%Y-%m-%d %H:%M:%S.%f",
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
