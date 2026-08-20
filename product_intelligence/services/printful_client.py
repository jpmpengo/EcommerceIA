class PrintfulClient:
    BASE_URL = "https://api.printful.com"

    def __init__(
        self,
        api_token,
        http_client,
    ):
        self.api_token = api_token
        self.http_client = http_client

    def _headers(
        self,
    ):
        return {
            "Authorization": (
                f"Bearer {self.api_token}"
            ),
        }

    def get_products(
        self,
    ):
        url = (
            f"{self.BASE_URL}/products"
        )

        response = self.http_client.get(
            url,
            headers=self._headers(),
        )

        data = response.json()

        if not isinstance(data, dict):
            return []

        products = data.get("result")

        if not isinstance(products, list):
            return []

        return products

    def get_product(
        self,
        product_id,
    ):
        url = (
            f"{self.BASE_URL}/products/"
            f"{product_id}"
        )

        response = self.http_client.get(
            url,
            headers=self._headers(),
        )

        data = response.json()

        if not isinstance(data, dict):
            return None

        result = data.get("result")

        if not isinstance(result, dict):
            return None

        return result

    def get_shipping_rates(
        self,
        variant_id,
        destination_country,
        quantity=1,
        currency="USD",
    ):
        url = (
            f"{self.BASE_URL}"
            "/v2/shipping-rates"
        )

        payload = {
            "recipient": {
                "country_code": (
                    destination_country
                ),
            },
            "order_items": [
                {
                    "source": "catalog",
                    "catalog_variant_id": (
                        variant_id
                    ),
                    "quantity": quantity,
                },
            ],
            "currency": currency,
        }

        response = self.http_client.post(
            url,
            json=payload,
            headers=self._headers(),
        )

        data = response.json()

        if not isinstance(
            data,
            dict,
        ):
            return []

        rates = data.get(
            "data"
        )

        if not isinstance(
            rates,
            list,
        ):
            return []

        return rates
