import os
import ssl

import httpx
import truststore

from orders.services.supplier_order_adapter_factory import SupplierOrderAdapterFactory
from orders.services.supplier_order_submission_service import SupplierOrderSubmissionService
from product_intelligence.services.cj_auth_client import CJAuthClient
from product_intelligence.services.cj_client import CJClient


class SupplierOrderSubmissionRunner:

    @classmethod
    def run_with_report(cls, order, sandbox=True, retry_failed=False, source="automatic"):
        api_key = os.getenv("CJ_API_KEY", "")
        if not api_key:
            raise ValueError("CJ_API_KEY est manquante.")
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=context, timeout=30.0) as http_client:
            token = CJAuthClient(api_key, http_client).get_access_token()
            service = SupplierOrderSubmissionService(
                SupplierOrderAdapterFactory(cj_client=CJClient(token, http_client))
            )
            results = service.submit(order, sandbox=sandbox, retry_failed=retry_failed, source=source)
            return {"supplier_orders": results, "failed": service.last_submission_failed_count}

    @classmethod
    def run(cls, order, sandbox=True, retry_failed=False, source="automatic"):
        api_key = os.getenv("CJ_API_KEY", "")
        if not api_key:
            raise ValueError("CJ_API_KEY est manquante.")

        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=context, timeout=30.0) as http_client:
            token = CJAuthClient(api_key, http_client).get_access_token()
            service = SupplierOrderSubmissionService(
                SupplierOrderAdapterFactory(
                    cj_client=CJClient(token, http_client),
                )
            )
            results = service.submit(
                order,
                sandbox=sandbox,
                retry_failed=retry_failed,
                source=source,
            )
            cls.last_submission_failed_count = service.last_submission_failed_count
            return results
