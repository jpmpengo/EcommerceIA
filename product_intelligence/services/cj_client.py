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
        self._last_request_at = None

    def _wait_for_rate_limit(self):
        now = time.monotonic()
        if self._last_request_at is not None:
            remaining = 1.0 - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
                now += remaining
        self._last_request_at = now

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
            self._wait_for_rate_limit()
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

                if status_code == 429:
                    delay = max(1.0, retry_after)
                    time.sleep(delay)
                    self._last_request_at = time.monotonic() - delay

                self._wait_for_rate_limit()
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
            self._wait_for_rate_limit()
            return self.http_client.post(
                url,
                json=json,
                headers=headers,
            )

        except httpx.RequestError:
            return None

    def _safe_patch(self, url, json=None, headers=None):
        try:
            self._wait_for_rate_limit()
            return self.http_client.patch(url, json=json, headers=headers)
        except httpx.RequestError:
            return None

    def calculate_freight_tip(
        self,
        product_sku,
        origin_country,
        destination_country,
        weight,
        product_properties,
        quantity=1,
    ):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/logistic/freightCalculateTip"
        )

        payload = {
            "reqDTOS": [
                {
                    "srcAreaCode": origin_country,
                    "destAreaCode": destination_country,
                    "weight": int(weight),
                    "productProp": list(product_properties),
                    "freightTrialSkuList": [
                        {
                            "skuQuantity": quantity,
                            "sku": product_sku,
                        }
                    ],
                }
            ]
        }

        response = self._safe_post(
            url,
            json=payload,
            headers=self._headers(),
        )

        if response is None:
            return []

        data = self._safe_json(response)

        if not self._is_successful_response(data):
            return []

        freight_options = data.get("data")

        if not isinstance(freight_options, list):
            return []

        return freight_options

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

    def create_order_v3(self, payload):
        if payload.get("isSandbox") != 1:
            raise ValueError("Protection CJ : isSandbox=1 est obligatoire.")

        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/shopping/order/createOrderV3"
        )
        response = self._safe_post(
            url,
            json=payload,
            headers={
                **self._headers(),
                "Content-Type": "application/json",
            },
        )
        if response is None:
            raise ValueError("CJ est injoignable pendant la création de commande.")
        data = self._safe_json(response)
        if not self._is_successful_response(data):
            message = (data or {}).get("message") or "Réponse CJ invalide."
            raise ValueError(f"Création de commande CJ refusée : {message}")
        result = data.get("data")
        if not isinstance(result, dict):
            raise ValueError("CJ n'a retourné aucune commande exploitable.")
        return result

    def get_order_detail(self, order_id):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/shopping/order/getOrderDetail"
        )
        return self._request_order_data("get", url, params={"orderId": order_id})

    def sandbox_simulate_pay(self, order_id):
        return self._sandbox_action(
            "/api2.0/v1/shopping/sandbox/simulatePay",
            {"orderId": order_id},
        )

    def confirm_order(self, order_id):
        url = f"{self.BASE_URL}/api2.0/v1/shopping/order/confirmOrder"
        response = self._safe_patch(
            url,
            json={"orderId": order_id},
            headers={**self._headers(), "Content-Type": "application/json"},
        )
        if response is None:
            raise ValueError("CJ est injoignable pendant la confirmation de commande.")
        data = self._safe_json(response)
        if not self._is_successful_response(data) or not data.get("data"):
            message = (data or {}).get("message") or "Réponse CJ invalide."
            raise ValueError(f"Confirmation de commande CJ refusée : {message}")
        return data["data"]

    def sandbox_update_status(self, order_id, target_status):
        if target_status not in {400, 500, 600, 700}:
            raise ValueError("Statut sandbox CJ invalide.")
        return self._sandbox_action(
            "/api2.0/v1/shopping/sandbox/updateStatus",
            {"orderId": order_id, "targetStatus": target_status},
        )

    def sandbox_update_track_number(self, order_id, track_number):
        if not track_number or len(track_number) > 64:
            raise ValueError("Le suivi sandbox doit contenir de 1 à 64 caractères.")
        return self._sandbox_action(
            "/api2.0/v1/shopping/sandbox/updateTrackNumber",
            {"orderId": order_id, "trackNumber": track_number},
        )

    def _sandbox_action(self, path, payload):
        url = f"{self.BASE_URL}{path}"
        response = self._safe_post(
            url,
            json=payload,
            headers={**self._headers(), "Content-Type": "application/json"},
        )
        if response is None:
            raise ValueError("CJ est injoignable pendant l'opération sandbox.")
        data = self._safe_json(response)
        if not self._is_successful_response(data) or data.get("data") is not True:
            message = (data or {}).get("message") or "Réponse CJ invalide."
            raise ValueError(f"Opération sandbox CJ refusée : {message}")
        return True

    def _request_order_data(self, method, url, params=None):
        if method != "get":
            raise ValueError("Méthode CJ non prise en charge.")
        response = self._safe_get(url, params=params, headers=self._headers())
        if response is None:
            raise ValueError("CJ est injoignable pendant la lecture de commande.")
        data = self._safe_json(response)
        if not self._is_successful_response(data):
            message = (data or {}).get("message") or "Réponse CJ invalide."
            raise ValueError(f"Lecture de commande CJ refusée : {message}")
        result = data.get("data")
        if not isinstance(result, dict):
            raise ValueError("CJ n'a retourné aucun détail de commande.")
        return result

    def search_products(
        self,
        keyword,
        country_code=None,
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

        if country_code:
            params["countryCode"] = country_code

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
            "product_description": product.get("description") or "",
            "currency": (
                product.get("currency")
                or "USD"
            ),
        }

        if product.get("addMarkStatus") is not None:
            normalized["free_shipping"] = (
                product.get("addMarkStatus") == 1
            )

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

    def get_variant_by_id(self, variant_id):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/product/variant/queryByVid"
        )
        response = self._safe_get(
            url,
            params={"vid": variant_id},
            headers=self._headers(),
        )

        if response is None:
            return None

        data = self._safe_json(response)
        if not self._is_successful_response(data):
            return None

        variant = data.get("data")
        if isinstance(variant, list):
            variant = variant[0] if variant else None

        return variant if isinstance(variant, dict) else None

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
        country_code=None,
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

        if country_code:
            matching_stock = next(
                (
                    item
                    for item in stock_data
                    if isinstance(item, dict)
                    and item.get("countryCode") == country_code
                ),
                None,
            )

            if matching_stock is None:
                return None

            return matching_stock.get(
                "totalInventoryNum"
            )

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





