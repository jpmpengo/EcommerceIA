from django.conf import settings
from orders.services.reception_monitoring_runner import ReceptionMonitoringRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelineReceptionNotificationStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        if not getattr(settings, "ORDER_RECEPTION_AUTO_EMAIL_ENABLED", False):
            return result
        report = ReceptionMonitoringRunner.run_notifications("http://127.0.0.1:8000")
        result.operations_effectuees = report["sent"]
        for error in report["errors"]:
            result.incidents.append("Commande {} : notification impossible - {}".format(error["order_id"], error["error"]))
        return result
