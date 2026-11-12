from abc import ABC, abstractmethod


class SupplierOrderAdapter(ABC):
    """Contrat commun aux fournisseurs capables de recevoir une commande."""

    @abstractmethod
    def build_payload(self, supplier_order, preparations):
        raise NotImplementedError

    @abstractmethod
    def submit(self, payload):
        raise NotImplementedError


class CJSupplierOrderAdapter(SupplierOrderAdapter):
    def __init__(self, client, sandbox=True):
        if not sandbox:
            raise ValueError("La transmission CJ réelle est désactivée.")
        self.client = client
        self.sandbox = sandbox

    def build_payload(self, supplier_order, preparations):
        order = supplier_order.order
        shop_amount = sum(
            preparation.order_item.price * preparation.quantity
            for preparation in preparations
        )
        methods = {
            preparation.supplier_offer.shipping_method
            for preparation in preparations
        }
        if "" in methods or not methods:
            raise ValueError("Le mode de transport fournisseur est manquant.")
        if len(methods) != 1:
            raise ValueError(
                "Les articles CJ d'une même commande doivent utiliser le même transport."
            )

        products = []
        for preparation in preparations:
            offer = preparation.supplier_offer
            if not offer.supplier_product_id:
                raise ValueError("Le VID CJ est manquant.")
            products.append(
                {
                    "vid": offer.supplier_product_id,
                    "quantity": preparation.quantity,
                    "storeLineItemId": str(preparation.order_item_id),
                    "storeProductId": str(preparation.order_item.product_id),
                    "storeProductName": preparation.order_item.product.name,
                    "storeSku": offer.supplier_sku,
                    "variantOptions": "-".join(
                        str(value)
                        for value in offer.variant_features.values()
                        if value
                    ),
                }
            )

        return {
            "orderNumber": supplier_order.idempotency_key,
            "shippingZip": order.postal_code,
            "shippingCountry": order.get_country_display(),
            "shippingCountryCode": order.country,
            "shippingProvince": order.city,
            "shippingCity": order.city,
            "shippingPhone": order.phone,
            "shippingCustomerName": f"{order.first_name} {order.last_name}".strip(),
            "shippingAddress": order.address,
            "email": order.email,
            "logisticName": methods.pop(),
            "fromCountryCode": "CN",
            "platform": "Api",
            "shopAmount": str(shop_amount),
            "iossType": 3,
            "iossNumber": "CJ-IOSS",
            "orderFlow": 1,
            "isSandbox": 1,
            "products": products,
        }

    def submit(self, payload):
        if payload.get("isSandbox") != 1:
            raise ValueError("Protection CJ : isSandbox=1 est obligatoire.")
        return self.client.create_order_v3(payload)

    def query(self, supplier_order_id):
        return self.client.get_order_detail(supplier_order_id)

    def simulate_pay(self, supplier_order_id):
        return self.client.sandbox_simulate_pay(supplier_order_id)

    def confirm(self, supplier_order_id):
        return self.client.confirm_order(supplier_order_id)

    def update_status(self, supplier_order_id, target_status):
        return self.client.sandbox_update_status(supplier_order_id, target_status)

    def update_tracking(self, supplier_order_id, tracking_number):
        return self.client.sandbox_update_track_number(
            supplier_order_id,
            tracking_number,
        )


class UnsupportedSupplierOrderAdapter(SupplierOrderAdapter):
    def __init__(self, supplier_name):
        self.supplier_name = supplier_name

    def build_payload(self, supplier_order, preparations):
        raise ValueError(
            f"Le fournisseur {self.supplier_name} ne permet pas encore la transmission."
        )

    def submit(self, payload):
        raise ValueError(
            f"Le fournisseur {self.supplier_name} ne permet pas encore la transmission."
        )
