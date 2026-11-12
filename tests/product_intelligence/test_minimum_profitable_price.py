from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.minimum_profitable_price import MinimumProfitablePriceService
from product_intelligence.services.opportunity_cost_calculation import OpportunityCostCalculationService


class MinimumProfitablePriceServiceTests(SimpleTestCase):

    def test_finds_minimum_price_for_ten_percent_margin(self):
        cost_service = OpportunityCostCalculationService(
            vat_rate=Decimal("0.20"),
            import_duty_rate=Decimal("0"),
            payment_rate=Decimal("0.015"),
            payment_fixed_fee=Decimal("0.25"),
            return_reserve_rate=Decimal("0.05"),
            safety_reserve_rate=Decimal("0.05"),
        )
        service = MinimumProfitablePriceService(
            cost_calculation_service=cost_service,
        )

        result = service.calculate(
            base_cost=Decimal("7.82"),
            currency="EUR",
            import_duty=Decimal("0.00"),
            minimum_margin_rate=Decimal("10.00"),
            minimum_profit=Decimal("0.01"),
        )

        self.assertEqual(result["decision_price"], Decimal("12.36"))
        self.assertEqual(result["cost_analysis"]["projected_margin_rate"], Decimal("10.00"))
        self.assertGreaterEqual(result["cost_analysis"]["projected_profit"], Decimal("0.01"))
