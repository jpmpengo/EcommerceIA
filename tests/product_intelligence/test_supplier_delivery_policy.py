from django.test import SimpleTestCase

from product_intelligence.services.supplier_delivery_policy import (
    SupplierDeliveryPolicyService,
)


class SupplierDeliveryPolicyServiceTests(
    SimpleTestCase
):

    def setUp(self):
        self.service = (
            SupplierDeliveryPolicyService(
                preferred_maximum_days=10,
                absolute_maximum_days=20,
            )
        )

    def test_accepts_delivery_within_ten_days(
        self,
    ):
        self.assertEqual(
            self.service.evaluate(
                shipping_days=10,
            ),
            {
                "status": "accepted",
                "reason": "",
                "score_penalty": 0,
            },
        )

    def test_marks_delivery_up_to_twenty_days_as_slow(
        self,
    ):
        self.assertEqual(
            self.service.evaluate(
                shipping_days=15,
            ),
            {
                "status": "slow",
                "reason": (
                    "Délai de livraison de "
                    "15 jours supérieur au "
                    "délai préféré de 10 jours."
                ),
                "score_penalty": 15,
            },
        )

    def test_rejects_delivery_over_twenty_days(
        self,
    ):
        self.assertEqual(
            self.service.evaluate(
                shipping_days=21,
            ),
            {
                "status": "rejected",
                "reason": (
                    "Délai de livraison de "
                    "21 jours supérieur au "
                    "maximum accepté de 20 jours."
                ),
                "score_penalty": None,
            },
        )

    def test_marks_unknown_delivery_incomplete(
        self,
    ):
        self.assertEqual(
            self.service.evaluate(
                shipping_days=None,
            ),
            {
                "status": "incomplete",
                "reason": (
                    "Délai de livraison manquant."
                ),
                "score_penalty": None,
            },
        )

    def test_default_policy_marks_fifty_days_as_fallback(
        self,
    ):
        service = SupplierDeliveryPolicyService()

        self.assertEqual(
            service.evaluate(50)["status"],
            "fallback",
        )

    def test_default_policy_rejects_more_than_fifty_days(
        self,
    ):
        service = SupplierDeliveryPolicyService()

        self.assertEqual(
            service.evaluate(51)["status"],
            "rejected",
        )
