from decimal import Decimal


class MinimumProfitablePriceService:

    STEP = Decimal("0.01")

    def __init__(self, cost_calculation_service):
        self.cost_calculation_service = cost_calculation_service

    def calculate(
        self,
        base_cost,
        currency,
        import_duty,
        minimum_margin_rate,
        minimum_profit,
    ):
        price = self.cost_calculation_service.calculate_minimum_profitable_price(base_cost=base_cost, import_duty=import_duty)
        cost_analysis = self.cost_calculation_service.calculate(decision_price=price, base_cost=base_cost, currency=currency, import_duty=import_duty)
        if cost_analysis["projected_profit"] <= 0:
            raise ValueError("Prix minimum rentable sans benefice positif.")
        return {"decision_price": price, "cost_analysis": cost_analysis}
