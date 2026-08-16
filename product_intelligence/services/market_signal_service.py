from decimal import Decimal





class MarketSignalService:

    @staticmethod
    def analyze(observation):
        snapshots = list(
            observation.snapshots
            .order_by("-observed_at")[:2]
        )

        if len(snapshots) < 2:
            return {
                "previous_price": None,
                "current_price": (
                    snapshots[0].observed_price
                    if snapshots
                    else None
                ),
                "price_change": None,
                "direction": "unknown",
            }

        current = snapshots[0].observed_price
        previous = snapshots[1].observed_price

        price_change = current - previous

        if previous == Decimal("0"):
            price_change_percent = None
        else:
            price_change_percent = (
                (price_change / previous)
                * Decimal("100")
            ).quantize(
                Decimal("0.01")
        )

        if price_change < Decimal("0"):
            direction = "down"
        elif price_change > Decimal("0"):
            direction = "up"
        else:
            direction = "stable"

        return {
            "previous_price": previous,
            "current_price": current,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "direction": direction,
        }

