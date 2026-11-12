from orders.services.paid_order_pipeline_runner import PaidOrderPipelineRunner
from orders.services.reception_monitoring_runner import ReceptionMonitoringRunner


class NightlyOrderPipelineRunner:
    @classmethod
    def run(cls, limit=20, order_id=None, simulate_full_lifecycle=False, send_notifications=False, site_url=None):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limite invalide (1 a 100).")
        result = {"supplier": PaidOrderPipelineRunner.run(limit=limit, order_id=order_id, simulate_full_lifecycle=simulate_full_lifecycle)}
        if not site_url:
            raise ValueError("URL du site requise pour les notifications.")
        result["notifications"] = ReceptionMonitoringRunner.run_notifications(site_url, limit=limit, order_id=order_id)
        result["receptions"] = ReceptionMonitoringRunner.run(limit=limit, order_id=order_id)
        from orders.services.supplier_pipeline_satisfaction_step import SupplierPipelineSatisfactionStep
        satisfaction = SupplierPipelineSatisfactionStep.run(limit=limit, order_id=order_id, site_url=site_url)
        result["satisfaction"] = {"sent": satisfaction.operations_effectuees, "incidents": satisfaction.incidents}
        return result
