class WooCommerceClient:

    def __init__(self, api):
        self.api = api

    def get_products(self):
        response = self.api.get(
            "products"
        )

        response.raise_for_status()

        return response.json()

    def normalize_product(self, product):
        return {
            "external_id": str(product["id"]),
            "name": product.get("name", ""),
            "observed_price": product.get("price"),
            "currency": "EUR",
            "product_url": product.get("permalink", ""),
        }