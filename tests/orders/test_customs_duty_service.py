from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from orders.services.customs_duty_service import CustomsDutyService


class CustomsDutyServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = CustomsDutyService()

    def test_applies_three_euros_per_item_during_temporary_period(self):
        result = self.service.estimate(
            origin_country="CN", destination_country="FR",
            intrinsic_value=Decimal("1.96"), quantity=2,
            rule_date=date(2026, 8, 27),
        )
        self.assertEqual(result["method"], "eu_temporary_flat_fee")
        self.assertEqual(result["amount"], Decimal("6.00"))
        self.assertEqual(result["unit_amount"], Decimal("3.00"))

    def test_keeps_pre_july_2026_low_value_exemption(self):
        result = self.service.estimate(
            origin_country="CN", destination_country="FR",
            intrinsic_value=Decimal("100.00"), quantity=1,
            rule_date=date(2026, 6, 30),
        )
        self.assertEqual(result["method"], "low_value_exemption")
        self.assertEqual(result["amount"], Decimal("0.00"))

    def test_intra_eu_has_no_import_duty(self):
        result = self.service.estimate(
            origin_country="ES", destination_country="FR",
            intrinsic_value=Decimal("40.00"), quantity=1,
            rule_date=date(2026, 8, 27),
        )
        self.assertEqual(result["method"], "intra_eu")
        self.assertEqual(result["amount"], Decimal("0.00"))

    def test_requires_tariff_data_above_150_euros(self):
        with self.assertRaisesMessage(ValueError, "code douanier"):
            self.service.estimate(
                origin_country="CN", destination_country="FR",
                intrinsic_value=Decimal("150.01"), quantity=1,
                rule_date=date(2026, 8, 27),
            )

    def test_refuses_to_guess_after_temporary_rule_expires(self):
        with self.assertRaisesMessage(ValueError, "expiré"):
            self.service.estimate(
                origin_country="CN", destination_country="FR",
                intrinsic_value=Decimal("10.00"), quantity=1,
                rule_date=date(2028, 7, 1),
            )
