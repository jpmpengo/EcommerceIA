import os
import ssl
import httpx
import truststore
from orders.models import SupplierOrder
from orders.models import OrderProcessingEvent
from orders.services.supplier_order_adapter_factory import SupplierOrderAdapterFactory
from orders.services.supplier_order_lifecycle_service import SupplierOrderLifecycleService
from orders.services.supplier_pipeline_result import SupplierPipelineResult
from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient

class SupplierPipelineConfirmationStep:
    @staticmethod
    def run():
        result = SupplierPipelineResult()
        dossiers = SupplierOrder.objects.filter(mode="sandbox", status="submitted", order__paid=True).select_related("supplier").order_by("id")
        for dossier in dossiers:
            if OrderProcessingEvent.objects.filter(supplier_order=dossier, event_type="supplier_order_confirmed").exists():
                continue
            if dossier.supplier_status in {"UNPAID", "UNSHIPPED", "SHIPPED", "DELIVERED"}:
                continue
            if not dossier.supplier_order_id:
                result.incidents.append("Dossier {} : identifiant CJ manquant".format(dossier.id))
                continue
            try:
                api_key = os.getenv("CJ_API_KEY", "")
                if not api_key:
                    raise ValueError("CJ_API_KEY manquante")
                context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                with httpx.Client(verify=context, timeout=30.0) as http_client:
                    token = CJAuthClient(api_key, http_client).get_access_token()
                    service = SupplierOrderLifecycleService(SupplierOrderAdapterFactory(cj_client=CJClient(token, http_client)))
                    detail = service.sync(dossier)
                    statut = str(detail.get("orderStatus") or "")
                    if statut == "CREATED":
                        service.confirm(dossier, source="automatic")
                        result.operations_effectuees += 1
                    elif statut not in {"UNPAID", "UNSHIPPED", "SHIPPED", "DELIVERED"}:
                        result.incidents.append("Dossier {} : statut CJ non reconnu ({})".format(dossier.id, statut))
            except Exception as error:
                result.incidents.append("Dossier {} : confirmation CJ impossible - {}".format(dossier.id, error))
        return result
