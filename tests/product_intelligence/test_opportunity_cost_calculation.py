from decimal import Decimal

from django.test import SimpleTestCase

from product_intelligence.services.opportunity_cost_calculation import (
    OpportunityCostCalculationService,
)


class OpportunityCostCalculationServiceTests(
    SimpleTestCase
):

    def test_calculates_all_configured_costs(
        self,
    ):
        service = (
            OpportunityCostCalculationService(
                vat_rate=Decimal("0.20"),
                import_duty_rate=Decimal("0.04"),
                payment_rate=Decimal("0.015"),
                payment_fixed_fee=Decimal("0.25"),
                return_reserve_rate=Decimal("0.05"),
                safety_reserve_rate=Decimal("0.05"),
            )
        )

        result = service.calculate(
            decision_price=Decimal("25.50"),
            base_cost=Decimal("16.86"),
            currency="EUR",
        )

        self.assertEqual(
            result,
            {
                "currency": "EUR",
                "decision_price": Decimal("25.50"),
                "net_revenue": Decimal("21.25"),
                "vat_amount": Decimal("4.25"),
                "base_cost": Decimal("16.86"),
                "import_duty": Decimal("0.67"),
                "payment_fee": Decimal("0.63"),
                "return_reserve": Decimal("1.28"),
                "safety_reserve": Decimal("0.84"),
                "total_costs": Decimal("20.28"),
                "projected_profit": Decimal("0.97"),
                "projected_margin_rate": Decimal("4.56"),
            },
        )

    def test_supports_zero_optional_rates(
        self,
    ):
        service = (
            OpportunityCostCalculationService(
                vat_rate=Decimal("0"),
                import_duty_rate=Decimal("0"),
                payment_rate=Decimal("0"),
                payment_fixed_fee=Decimal("0"),
                return_reserve_rate=Decimal("0"),
                safety_reserve_rate=Decimal("0"),
            )
        )

        result = service.calculate(
            decision_price=Decimal("20.00"),
            base_cost=Decimal("8.00"),
            currency="EUR",
        )

        self.assertEqual(
            result["net_revenue"],
            Decimal("20.00"),
        )

        self.assertEqual(
            result["total_costs"],
            Decimal("8.00"),
        )

        self.assertEqual(
            result["projected_profit"],
            Decimal("12.00"),
        )

        self.assertEqual(
            result["projected_margin_rate"],
            Decimal("60.00"),
        )

    def test_rejects_invalid_rate(
        self,
    ):
        with self.assertRaisesMessage(
            ValueError,
            (
                "Les taux doivent être compris "
                "entre 0 et 1."
            ),
        ):
            OpportunityCostCalculationService(
                vat_rate=Decimal("1.20"),
                import_duty_rate=Decimal("0"),
                payment_rate=Decimal("0"),
                payment_fixed_fee=Decimal("0"),
                return_reserve_rate=Decimal("0"),
                safety_reserve_rate=Decimal("0"),
            )