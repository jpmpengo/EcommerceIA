from decimal import (
    Decimal,
    ROUND_HALF_UP,
    ROUND_CEILING,
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
        import_duty=None,
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

        if import_duty is None:
            import_duty = self._money(base_cost * self.import_duty_rate)
        elif import_duty < 0:
            raise ValueError("Les droits de douane ne peuvent pas être négatifs.")
        else:
            import_duty = self._money(import_duty)

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

    def calculate_break_even_price(self, base_cost, import_duty=None):
        if base_cost < 0:
            raise ValueError("Le cout de base ne peut pas etre negatif.")
        duty = self._money(base_cost * self.import_duty_rate) if import_duty is None else self._money(import_duty)
        if duty < 0:
            raise ValueError("Les droits de douane ne peuvent pas etre negatifs.")
        fixed_costs = base_cost + duty + self.payment_fixed_fee + self._money(base_cost * self.safety_reserve_rate)
        coefficient = Decimal("1") / (Decimal("1") + self.vat_rate) - self.payment_rate - self.return_reserve_rate
        if coefficient <= 0:
            raise ValueError("Prix equilibre impossible avec les taux configures.")
        price = (fixed_costs / coefficient).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
        return price

    def calculate_minimum_profitable_price(self, base_cost, import_duty=None):
        break_even_price = self.calculate_break_even_price(base_cost, import_duty)
        return (break_even_price * Decimal("1.10")).quantize(self.MONEY_PRECISION, rounding=ROUND_CEILING)

    @classmethod
    def _money(
        cls,
        amount,
    ):
        return amount.quantize(
            cls.MONEY_PRECISION,
            rounding=ROUND_HALF_UP,
        )
