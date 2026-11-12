from unittest.mock import Mock, patch

from django.test import TestCase

from orders.services.supplier_preparation_runner import SupplierPreparationRunner


class SupplierPreparationRunnerTests(TestCase):
    @patch("orders.services.supplier_preparation_runner.SupplierPreparationService")
    @patch("orders.services.supplier_preparation_runner.httpx.Client")
    @patch("orders.services.supplier_preparation_runner.truststore.SSLContext")
    def test_run_prepares_all_order_items_with_source(
        self,
        ssl_context_class,
        http_client_class,
        preparation_service_class,
    ):
        item_a = Mock()
        item_b = Mock()
        order = Mock()
        order.items.all.return_value = [item_a, item_b]

        preparation_a = Mock()
        preparation_b = Mock()
        service = preparation_service_class.return_value
        service.prepare.side_effect = [preparation_a, preparation_b]

        http_client = Mock()
        http_client_class.return_value.__enter__.return_value = http_client

        result = SupplierPreparationRunner.run(
            order,
            source="manual",
        )

        self.assertEqual(result, [preparation_a, preparation_b])
        self.assertEqual(service.prepare.call_count, 2)
        service.prepare.assert_any_call(item_a, source="manual")
        service.prepare.assert_any_call(item_b, source="manual")
