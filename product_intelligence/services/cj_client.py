import httpx
import time


class CJClient:
    BASE_URL = "https://developers.cjdropshipping.com"

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
    }

    def __init__(
        self,
        access_token,
        http_client,
    ):
        self.access_token = access_token
        self.http_client = http_client

    def _headers(self):
        return {
            "CJ-Access-Token": self.access_token,
        }

    def _safe_json(
        self,
        response,
    ):
        try:
            data = response.json()
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None

        return data

    def _safe_get(
        self,
        url,
        params=None,
        headers=None,
    ):
        try:
            response = self.http_client.get(
                url,
                params=params,
                headers=headers,
            )

            status_code = getattr(
                response,
                "status_code",
                200,
            )

            if (
                status_code
                in self.RETRYABLE_STATUS_CODES
            ):
                retry_after = 0.0

                if status_code == 429:
                    response_headers = getattr(
                        response,
                        "headers",
                        {},
                    )

                    retry_after_value = (
                        response_headers.get(
                            "Retry-After"
                        )
                    )

                    if retry_after_value is not None:
                        try:
                            retry_after = float(
                                retry_after_value
                            )
                        except (
                            TypeError,
                            ValueError,
                        ):
                            retry_after = 0.0

                if retry_after > 0:
                    time.sleep(
                        retry_after
                    )

                response = self.http_client.get(
                    url,
                    params=params,
                    headers=headers,
                )

            return response

        except httpx.RequestError:
            return None

    def _safe_post(
        self,
        url,
        json=None,
        headers=None,
    ):
        try:
            return self.http_client.post(
                url,
                json=json,
                headers=headers,
            )

        except httpx.RequestError:
            return None

    def calculate_freight(
        self,
        variant_id,
        origin_country,
        destination_country,
        quantity=1,
    ):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/logistic/freightCalculate"
        )

        payload = {
            "startCountryCode": origin_country,
            "endCountryCode": destination_country,
            "products": [
                {
                    "quantity": quantity,
                    "vid": variant_id,
                },
            ],
        }

        response = self._safe_post(
            url,
            json=payload,
            headers=self._headers(),
        )

        if response is None:
            return []

        data = self._safe_json(
            response
        )

        if not self._is_successful_response(
            data
        ):
            return []

        freight_options = data.get(
            "data"
        )

        if not isinstance(
            freight_options,
            list,
        ):
            return []

        return freight_options

    def search_products(
        self,
        keyword,
    ):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/product/listV2"
        )

        params = {
            "page": 1,
            "size": 20,
            "keyWord": keyword,
        }

        response = self._safe_get(
            url,
            params=params,
            headers=self._headers(),
        )

        if response is None:
            return []

        data = self._safe_json(
            response
        )

        if not self._is_successful_response(
            data
        ):
            return []

        if not data:
            return []

        cj_data = data.get("data")

        if not cj_data:
            return []

        content = cj_data.get("content")

        if not isinstance(
            content,
            list,
        ):
            return []

        content = cj_data.get("content")

        if not content:
            return []

        first_content = (
            content[0]
            or {}
        )

        if not isinstance(
            first_content,
            dict,
        ):
            return []

        product_list = first_content.get(
            "productList",
            [],
        )

        if not isinstance(
            product_list,
            list,
        ):
            return []

        return product_list

    def get_product_detail(
        self,
        product_id,
    ):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/product/query"
        )

        params = {
            "pid": product_id,
        }

        response = self._safe_get(
            url,
            params=params,
            headers=self._headers(),
        )

        if response is None:
            return None

        data = self._safe_json(
            response
        )

        if not self._is_successful_response(
            data
        ):
            return None

        if not data:
            return None

        return data.get(
            "data"
        )

    def normalize_product(
        self,
        product,
    ):
        external_id = (
            product.get("id")
            or product.get("pid")
        )

        name = (
            product.get("nameEn")
            or product.get("productNameEn")
            or ""
        )

        image_url = (
            product.get("bigImage")
            or product.get("productImage")
            or ""
        )

        normalized = {
            "external_id": external_id,
            "name": name,
            "image_url": image_url,
            "currency": (
                product.get("currency")
                or "USD"
            ),
        }

        if product.get(
            "sellPrice"
        ) is not None:
            normalized[
                "purchase_price"
            ] = product["sellPrice"]

        return normalized

    def get_product_variants(
        self,
        product_id,
    ):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/product/variant/query"
        )

        params = {
            "pid": product_id,
        }

        response = self._safe_get(
            url,
            params=params,
            headers=self._headers(),
        )

        if response is None:
            return []

        data = self._safe_json(
            response
        )

        if not self._is_successful_response(
            data
        ):
            return []

        if not data:
            return []

        variants = data.get(
            "data"
        )

        if not isinstance(
            variants,
            list,
        ):
            return []

        if not variants:
            return []

        return variants

    def normalize_variant(
        self,
        variant,
    ):
        return {
            "variant_id": variant["vid"],
            "product_id": variant["pid"],
            "name": variant["variantNameEn"],
            "purchase_price": (
                variant["variantSellPrice"]
            ),
        }

    def get_variant_stock(
        self,
        variant_id,
    ):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/product/stock/queryByVid"
        )

        params = {
            "vid": variant_id,
        }

        response = self._safe_get(
            url,
            params=params,
            headers=self._headers(),
        )

        if response is None:
            return None

        data = self._safe_json(
            response
        )

        if not self._is_successful_response(
            data
        ):
            return None

        if not data:
            return None

        stock_data = data.get(
            "data"
        )
    
        if not isinstance(
            stock_data,
            list,
        ):
            return None

        if not stock_data:
            return None

        first_stock = (
            stock_data[0]
            or {}
        )

        if not isinstance(
            first_stock,
            dict,
        ):
            return None

        return first_stock.get(
            "totalInventoryNum"
        )
    
    def _is_successful_response(self, data):
        if not data:
            return False

        if data.get("result") is False:
            return False

        code = data.get("code")

        if code is not None and code != 200:
            return False

        return True





