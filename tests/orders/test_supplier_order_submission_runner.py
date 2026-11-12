from unittest.mock import Mock, patch

from django.test import TestCase

from orders.services.supplier_order_submission_runner import SupplierOrderSubmissionRunner


class SupplierOrderSubmissionRunnerTests(TestCase):

    @patch("orders.services.supplier_order_submission_runner.SupplierOrderSubmissionService")
    @patch("orders.services.supplier_order_submission_runner.CJAuthClient")
    @patch("orders.services.supplier_order_submission_runner.CJClient")
    @patch("orders.services.supplier_order_submission_runner.httpx.Client")
    @patch("orders.services.supplier_order_submission_runner.truststore.SSLContext")
    @patch("orders.services.supplier_order_submission_runner.os.getenv")
    def test_run_submits_with_source_and_retry(
        self,
        getenv,
        ssl_context_class,
        http_client_class,
        cj_client_class,
        auth_client_class,
        submission_service_class,
    ):
        getenv.return_value = "CJ-KEY"
        order = Mock()
        supplier_orders = [Mock()]

        http_client = Mock()
        http_client_class.return_value.__enter__.return_value = http_client
        auth_client_class.return_value.get_access_token.return_value = "TOKEN"
        submission_service_class.return_value.submit.return_value = supplier_orders

        result = SupplierOrderSubmissionRunner.run(
            order,
            sandbox=True,
            retry_failed=True,
            source="manual",
        )

        self.assertEqual(result, supplier_orders)
        submission_service_class.return_value.submit.assert_called_once_with(
            order,
            sandbox=True,
            retry_failed=True,
            source="manual",
        )
