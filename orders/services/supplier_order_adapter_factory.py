from orders.services.supplier_order_adapters import (
    CJSupplierOrderAdapter,
    UnsupportedSupplierOrderAdapter,
)


class SupplierOrderAdapterFactory:
    def __init__(self, cj_client=None):
        self.cj_client = cj_client

    def create(self, supplier, sandbox=True):
        name = (supplier.name or "").strip().lower()
        if name == "cjdropshipping":
            if self.cj_client is None:
                raise ValueError("Le client API CJ n'est pas configuré.")
            return CJSupplierOrderAdapter(self.cj_client, sandbox=sandbox)
        return UnsupportedSupplierOrderAdapter(supplier.name)
