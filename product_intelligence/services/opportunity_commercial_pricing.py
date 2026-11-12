from decimal import Decimal, ROUND_HALF_UP
from product_intelligence.services.pricing_policy import get_market_price_reference, LOW_COMPETITION_MULTIPLIER, MODERATE_COMPETITION_MULTIPLIER


class OpportunityCommercialPricingService:
    PRECISION = Decimal("0.01")

    @classmethod
    def calculate(cls, saturation_level, minimum_profitable_price, commercial_median_price=None, market_summary=None, supplier_shipping_days=None):
        floor = Decimal(str(minimum_profitable_price))
        if saturation_level in ("high", "very_high"):
            summary = market_summary or {}
            competitor_minimum = summary.get("minimum_price")
            delays = [int(c["shipping_days_max"]) for c in summary.get("shipping_comparables", []) if c.get("shipping_days_max") is not None]
            target = floor
            policy = "minimum_profitable"
            if competitor_minimum is not None and supplier_shipping_days is not None and delays:
                competitor_minimum = Decimal(str(competitor_minimum))
                if Decimal(str(supplier_shipping_days)) <= max(delays):
                    target = competitor_minimum
                    policy = "competitor_minimum_delivery"
                else:
                    target = (competitor_minimum * Decimal("0.90")).quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
                    policy = "competitor_minimum_minus_10_delivery"
        elif saturation_level in ("low", "very_low", "moderate"):
            reference = get_market_price_reference()
            summary = market_summary or {}
            field = {"minimum": "minimum_price", "median": "commercial_median_price", "maximum": "maximum_price"}[reference]
            value = commercial_median_price if reference == "median" and commercial_median_price is not None else summary.get(field)
            if value is None:
                return {"status": "incomplete", "reason": "Reference de prix du marche indisponible : " + reference}
            coefficient = LOW_COMPETITION_MULTIPLIER if saturation_level in ("low", "very_low") else MODERATE_COMPETITION_MULTIPLIER
            target = (Decimal(str(value)) * coefficient).quantize(cls.PRECISION, rounding=ROUND_HALF_UP)
            policy = reference + ("_plus_10" if saturation_level in ("low", "very_low") else "_minus_10")
        else:
            return {"status": "incomplete", "reason": "Niveau de concurrence indéterminé."}
        price = max(target, floor)
        return {"status": "ready", "recommended_price": price, "minimum_profitable_price": floor, "policy": policy, "floor_applied": target < floor}
