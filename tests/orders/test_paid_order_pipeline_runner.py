from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from orders.services.paid_order_pipeline_runner import PaidOrderPipelineRunner

class PaidOrderPipelineRunnerTests(SimpleTestCase):
    @patch("orders.services.paid_order_pipeline_runner.SupplierOrderMonitoringRunner.run")
    @patch("orders.services.paid_order_pipeline_runner.SupplierOrderSubmissionRunner.run")
    @patch("orders.services.paid_order_pipeline_runner.SupplierOrder.objects.filter")
    @patch("orders.services.paid_order_pipeline_runner.PaidOrderPipelineRunner.get_orders")
    def test_blocked_order_is_not_resubmitted(self, get_orders, supplier_filter, submit, monitor):
        order = Mock(id=24)
        order.items.all.return_value = [Mock()]
        get_orders.return_value = [order]
        supplier_filter.return_value.exists.return_value = True
        monitor.return_value = {"selected": 0, "synced": 0, "failed": 0}
        result = PaidOrderPipelineRunner.run(limit=1)
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["submitted"], 0)
        submit.assert_not_called()
        monitor.assert_called_once_with(limit=1)
