from decimal import Decimal

from product_intelligence.services.opportunity_cost_calculation import OpportunityCostCalculationService
from product_intelligence.services.opportunity_commercial_pricing import OpportunityCommercialPricingService
from product_intelligence.services.opportunity_commercial_score import OpportunityCommercialScoreService


class OpportunityCommercialRecalculationService:
    @classmethod
    def calculate(cls, opportunity, market_summary=None):
        base_cost = Decimal(str(opportunity.supplier_price)) + Decimal(str(opportunity.shipping_cost))
        customs_included = bool(opportunity.supplier_offer and opportunity.supplier_offer.customs_included)
        if not customs_included:
            return {"status": "incomplete", "reason": "Droits de douane a verifier avant recalcul."}
        calculator = OpportunityCostCalculationService(vat_rate=Decimal("0.20"), import_duty_rate=Decimal("0"), payment_rate=Decimal("0.015"), payment_fixed_fee=Decimal("0.25"), return_reserve_rate=Decimal("0.05"), safety_reserve_rate=Decimal("0.05"))
        break_even = calculator.calculate_break_even_price(base_cost, import_duty=Decimal("0"))
        minimum = calculator.calculate_minimum_profitable_price(base_cost, import_duty=Decimal("0"))
        pricing = OpportunityCommercialPricingService.calculate(saturation_level=opportunity.saturation_level, minimum_profitable_price=minimum, market_summary=market_summary, supplier_shipping_days=opportunity.supplier_offer.shipping_days)
        if pricing["status"] != "ready":
            return pricing
        costs = calculator.calculate(decision_price=pricing["recommended_price"], base_cost=base_cost, currency="EUR", import_duty=Decimal("0"))
        additional_costs = sum((costs[k] for k in ("vat_amount", "import_duty", "payment_fee", "return_reserve", "safety_reserve")), Decimal("0"))
        total_cost = base_cost + additional_costs
        score_margin = (pricing["recommended_price"] - total_cost) / total_cost * Decimal("100") if total_cost > 0 else Decimal("0")
        score = OpportunityCommercialScoreService.calculate(score_margin, opportunity.demand_score, opportunity.saturation_level)
        return {"status": "ready", "break_even_price": break_even, "minimum_profitable_price": minimum, "recommended_price": pricing["recommended_price"], "pricing_policy": pricing["policy"], "floor_applied": pricing["floor_applied"], "other_costs": additional_costs, "projected_profit": costs["projected_profit"], "projected_margin_rate": costs["projected_margin_rate"], "opportunity_score": score}
