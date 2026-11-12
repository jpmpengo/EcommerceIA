from orders.services.reception_monitoring_runner import ReceptionMonitoringRunner
from orders.services.supplier_pipeline_result import SupplierPipelineResult


class SupplierPipelineReceptionAssumptionStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        report = ReceptionMonitoringRunner.run(limit=100)
        result.operations_effectuees = report["assumed"]
        if report["failed"]:
            result.incidents.append("Reception presumee : {} traitement(s) en echec".format(report["failed"]))
        return result
