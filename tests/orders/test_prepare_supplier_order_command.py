from unittest.mock import Mock, patch

from django.core.management import call_command
from django.test import TestCase


class PrepareSupplierOrderCommandTests(TestCase):

    @patch("orders.management.commands.prepare_supplier_order.SupplierPreparationRunner")
    @patch("orders.management.commands.prepare_supplier_order.Order.objects.prefetch_related")
    def test_command_delegates_to_runner_with_manual_source(
        self,
        prefetch_related,
        runner,
    ):
        order = Mock()
        prefetch_related.return_value.get.return_value = order
        runner.run.return_value = []

        call_command(
            "prepare_supplier_order",
            23,
            vat_rate="0.20",
        )

        runner.run.assert_called_once_with(
            order,
            source="manual",
            vat_rate="0.20",
        )
