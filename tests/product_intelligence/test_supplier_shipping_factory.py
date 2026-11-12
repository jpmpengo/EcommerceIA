from unittest.mock import (
    Mock,
    patch,
)

from django.test import SimpleTestCase

from product_intelligence.services.aw_shipping_estimator import (
    AWShippingEstimator,
)
from product_intelligence.services.cj_shipping_estimator import (
    CJShippingEstimator,
)
from product_intelligence.services.multi_supplier_shipping import (
    MultiSupplierShippingService,
)
from product_intelligence.services.printful_shipping_estimator import (
    PrintfulShippingEstimator,
)
from product_intelligence.services.supplier_shipping_factory import (
    SupplierShippingFactory,
)


class SupplierShippingFactoryTests(
    SimpleTestCase
):

    @patch(
        (
            "product_intelligence.services."
            "supplier_shipping_factory."
            "PrintfulClient"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_shipping_factory."
            "CJClient"
        )
    )
    @patch(
        (
            "product_intelligence.services."
            "supplier_shipping_factory."
            "CJAuthClient"
        )
    )
    def test_builds_available_shipping_estimators(
        self,
        cj_auth_client_class,
        cj_client_class,
        printful_client_class,
    ):
        http_client = Mock()

        (
            cj_auth_client_class
            .return_value
            .get_access_token
            .return_value
        ) = "test-access-token"

        service = SupplierShippingFactory.build(
            http_client=http_client,
            cj_api_key="test-cj-key",
            printful_api_token=(
                "test-printful-token"
            ),
            maximum_shipping_days=20,
        )

        self.assertIsInstance(
            service,
            MultiSupplierShippingService,
        )

        self.assertEqual(
            len(service.estimators),
            2,
        )

        self.assertIsInstance(
            service.estimators[0],
            CJShippingEstimator,
        )

        self.assertEqual(
            (
                service.estimators[0]
                .maximum_shipping_days
            ),
            20,
        )

        self.assertIsInstance(
            service.estimators[1],
            PrintfulShippingEstimator,
        )

        cj_auth_client_class.assert_called_once_with(
            api_key="test-cj-key",
            http_client=http_client,
        )

        cj_client_class.assert_called_once_with(
            access_token="test-access-token",
            http_client=http_client,
        )

        printful_client_class.assert_called_once_with(
            api_token="test-printful-token",
            http_client=http_client,
        )

    def test_builds_empty_service_without_credentials(
        self,
    ):
        service = SupplierShippingFactory.build(
            http_client=Mock(),
        )

        self.assertIsInstance(
            service,
            MultiSupplierShippingService,
        )

        self.assertEqual(
            service.estimators,
            [],
        )

    def test_builds_aw_shipping_estimator_when_configured(self):
        service = SupplierShippingFactory.build(
            http_client=Mock(),
            aw_api_token="aw-test-token",
        )

        self.assertEqual(
            len(service.estimators),
            1,
        )
        self.assertIsInstance(
            service.estimators[0],
            AWShippingEstimator,
        )

