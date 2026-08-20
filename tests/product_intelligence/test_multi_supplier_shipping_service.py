from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.multi_supplier_shipping import (
    MultiSupplierShippingService,
)


class MultiSupplierShippingServiceTests(
    SimpleTestCase
):

    def test_uses_matching_supplier_shipping_estimator(
        self,
    ):
        offer = Mock()

        cj_estimator = Mock()
        cj_estimator.can_handle.return_value = True
        cj_estimator.estimate.return_value = {
            "cost": "8.50",
            "currency": "USD",
            "shipping_days": 8,
            "shipping_country": "FR",
        }

        printful_estimator = Mock()
        printful_estimator.can_handle.return_value = False

        service = MultiSupplierShippingService(
            estimators=[
                cj_estimator,
                printful_estimator,
            ],
        )

        result = service.estimate(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        self.assertEqual(
            result,
            cj_estimator.estimate.return_value,
        )

        cj_estimator.can_handle.assert_called_once_with(
            offer
        )

        cj_estimator.estimate.assert_called_once_with(
            offer=offer,
            destination_country="FR",
            quantity=1,
        )

        printful_estimator.estimate.assert_not_called()
