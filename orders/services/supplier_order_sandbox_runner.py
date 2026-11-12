import os
import ssl

import httpx
import truststore

from orders.services.supplier_order_adapter_factory import SupplierOrderAdapterFactory
from orders.services.supplier_order_lifecycle_service import SupplierOrderLifecycleService
from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient


class SupplierOrderSandboxRunner:
    @staticmethod
    def run(supplier_order, action, tracking_number=None, source="automatic"):
        if action not in ("sync", "confirm", "pay", "processing", "ship", "tracking", "deliver"):
            raise ValueError("Action fournisseur non autorisee.")
        if supplier_order.mode != "sandbox":
            raise ValueError("Operation reservee au sandbox.")
        if supplier_order.status != "submitted" or not supplier_order.supplier_order_id:
            raise ValueError("Commande fournisseur non soumise.")
        api_key = os.getenv("CJ_API_KEY", "")
        if not api_key:
            raise ValueError("CJ_API_KEY est manquante.")
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=context, timeout=30.0) as http_client:
            token = CJAuthClient(api_key, http_client).get_access_token()
            service = SupplierOrderLifecycleService(SupplierOrderAdapterFactory(cj_client=CJClient(token, http_client)))
            if action == "sync":
                return service.sync(supplier_order)
            if action == "confirm":
                return service.confirm(supplier_order, source=source)
            if action == "pay":
                return service.simulate_pay(supplier_order, source=source)
            if action == "processing":
                return service.update_status(supplier_order, 400, source=source)
            if action == "ship":
                return service.update_status(supplier_order, 500, source=source)
            if action == "tracking":
                if not tracking_number:
                    raise ValueError("Numero de suivi manquant.")
                return service.update_tracking(supplier_order, tracking_number, source=source)
            if action == "deliver":
                return service.update_status(supplier_order, 600, source=source)
