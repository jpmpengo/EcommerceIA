from decimal import Decimal


class OpportunityScoreService:

    BASE_SCORE = Decimal("50.00")

    @classmethod
    def calculate(cls, signals):
        score = cls.BASE_SCORE

        direction = signals.get("direction")
        change_percent = signals.get(
            "price_change_percent"
        )

        if (
            direction == "down"
            and change_percent is not None
        ):
            score += min(
                abs(change_percent),
                Decimal("20.00"),
            )

        elif (
            direction == "up"
            and change_percent is not None
        ):
            score -= min(
                abs(change_percent),
                Decimal("20.00"),
            )

        score = max(
            Decimal("0.00"),
            min(
                score,
                Decimal("100.00"),
            ),
        )

        return score.quantize(
            Decimal("0.01")
        )

    @classmethod
    def explain(cls, signals):
        score = cls.calculate(
            signals
        )

        reasons = []

        direction = signals.get("direction")
        change_percent = signals.get(
            "price_change_percent"
        )

        if (
            direction == "down"
            and change_percent is not None
        ):
            reasons.append(
                (
                    "Baisse de prix de "
                    f"{abs(change_percent):.2f} %"
                )
            )

        elif (
            direction == "up"
            and change_percent is not None
        ):
            reasons.append(
                (
                    "Hausse de prix de "
                    f"{abs(change_percent):.2f} %"
                )
            )

        elif direction == "stable":
            reasons.append(
                "Prix stable"
            )

        return {
            "score": score,
            "reasons": reasons,
        }

        
