from decimal import (
    Decimal,
    ROUND_HALF_UP,
)


class OpportunityCostCalculationService:

    MONEY_PRECISION = Decimal("0.01")

    def __init__(
        self,
        vat_rate,
        import_duty_rate,
        payment_rate,
        payment_fixed_fee,
        return_reserve_rate,
        safety_reserve_rate,
    ):
        rates = [
            vat_rate,
            import_duty_rate,
            payment_rate,
            return_reserve_rate,
            safety_reserve_rate,
        ]

        if any(
            rate < 0 or rate > 1
            for rate in rates
        ):
            raise ValueError(
                (
                    "Les taux doivent être compris "
                    "entre 0 et 1."
                )
            )

        if payment_fixed_fee < 0:
            raise ValueError(
                (
                    "Les frais fixes de paiement "
                    "ne peuvent pas être négatifs."
                )
            )

        self.vat_rate = vat_rate

        self.import_duty_rate = (
            import_duty_rate
        )

        self.payment_rate = payment_rate

        self.payment_fixed_fee = (
            payment_fixed_fee
        )

        self.return_reserve_rate = (
            return_reserve_rate
        )

        self.safety_reserve_rate = (
            safety_reserve_rate
        )

    def calculate(
        self,
        decision_price,
        base_cost,
        currency,
    ):
        if decision_price <= 0:
            raise ValueError(
                (
                    "Le prix décisionnel doit "
                    "être positif."
                )
            )

        if base_cost < 0:
            raise ValueError(
                (
                    "Le coût de base ne peut pas "
                    "être négatif."
                )
            )

        net_revenue = self._money(
            decision_price
            / (
                Decimal("1")
                + self.vat_rate
            )
        )

        vat_amount = self._money(
            decision_price
            - net_revenue
        )

        import_duty = self._money(
            base_cost
            * self.import_duty_rate
        )

        payment_fee = self._money(
            (
                decision_price
                * self.payment_rate
            )
            + self.payment_fixed_fee
        )

        return_reserve = self._money(
            decision_price
            * self.return_reserve_rate
        )

        safety_reserve = self._money(
            base_cost
            * self.safety_reserve_rate
        )

        total_costs = self._money(
            base_cost
            + import_duty
            + payment_fee
            + return_reserve
            + safety_reserve
        )

        projected_profit = self._money(
            net_revenue
            - total_costs
        )

        projected_margin_rate = (
            projected_profit
            / net_revenue
            * Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        return {
            "currency": currency,
            "decision_price": (
                decision_price
            ),
            "net_revenue": net_revenue,
            "vat_amount": vat_amount,
            "base_cost": base_cost,
            "import_duty": import_duty,
            "payment_fee": payment_fee,
            "return_reserve": (
                return_reserve
            ),
            "safety_reserve": (
                safety_reserve
            ),
            "total_costs": total_costs,
            "projected_profit": (
                projected_profit
            ),
            "projected_margin_rate": (
                projected_margin_rate
            ),
        }

    @classmethod
    def _money(
        cls,
        amount,
    ):
        return amount.quantize(
            cls.MONEY_PRECISION,
            rounding=ROUND_HALF_UP,
        )