import hashlib
import time

import httpx


class EproloClient:
    BASE_URL = "https://openapi.eprolo.com"

    def __init__(
        self,
        api_key,
        api_secret,
        http_client,
        base_url=None,
        timestamp_factory=None,
    ):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.http_client = http_client
        self.base_url = (
            base_url or self.BASE_URL
        ).rstrip("/")
        self.timestamp_factory = (
            timestamp_factory
            or (lambda: int(time.time() * 1000))
        )

    def _authentication(self):
        timestamp = str(self.timestamp_factory())
        raw_signature = (
            self.api_key
            + timestamp
            + self.api_secret
        )
        signature = hashlib.md5(
            raw_signature.encode("utf-8")
        ).hexdigest()
        return timestamp, signature

    def _headers(self):
        return {
            "apiKey": self.api_key,
            "ContentType": "application/json",
            "Accept": "application/json",
            "User-Agent": "EcommerceIA/1.0",
        }

    def _get(self, path, params=None):
        timestamp, signature = (
            self._authentication()
        )
        signed_params = dict(params or {})
        signed_params.update(
            {
                "timestamp": timestamp,
                "sign": signature,
            }
        )

        try:
            response = self.http_client.get(
                f"{self.base_url}/{path.lstrip('/')}",
                params=signed_params,
                headers=self._headers(),
            )
        except httpx.RequestError:
            return None

        if getattr(response, "status_code", 200) != 200:
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        if not isinstance(payload, dict):
            return None

        if str(payload.get("code")) != "0":
            return None

        return payload.get("data")

    def get_catalog_page(
        self,
        page=1,
        ware_type_id=None,
        ware_type_two_id=None,
    ):
        params = {"page": page}
        if ware_type_id is not None:
            params["wareTypeId"] = ware_type_id
        if ware_type_two_id is not None:
            params["wareTypeTwoId"] = (
                ware_type_two_id
            )
        data = self._get(
            "/eprolo_product_list.html",
            params=params,
        )
        return data if isinstance(data, list) else []

    def search_products(
        self,
        keyword,
        matching_service,
        ware_type_id,
        ware_type_two_id,
        max_pages=5,
        max_results=20,
    ):
        matches = []
        for page in range(1, max_pages + 1):
            products = self.get_catalog_page(
                page,
                ware_type_id=ware_type_id,
                ware_type_two_id=ware_type_two_id,
            )
            if not products:
                break

            for product in products:
                if not isinstance(product, dict):
                    continue
                if not self._belongs_to_category(
                    product,
                    ware_type_id=ware_type_id,
                    ware_type_two_id=(
                        ware_type_two_id
                    ),
                ):
                    continue
                if matching_service.is_relevant(
                    product_name=(
                        product.get("title") or ""
                    ),
                    search_keyword=keyword,
                ):
                    matches.append(product)
                    if len(matches) >= max_results:
                        return matches

        return matches

    @staticmethod
    def _category_ids(value):
        return {
            item.strip()
            for item in str(value or "").split(",")
            if item.strip()
        }

    def _belongs_to_category(
        self,
        product,
        ware_type_id,
        ware_type_two_id,
    ):
        parent_ids = self._category_ids(
            product.get("wareTypeId")
        )
        child_ids = self._category_ids(
            product.get("wareTypeTwoId")
        )
        return (
            str(ware_type_id) in parent_ids
            and str(ware_type_two_id) in child_ids
        )

    def get_shipping_rates(
        self,
        product_id,
        variant_id,
        destination_country,
    ):
        data = self._get(
            "/get_product_shiping_fees.html",
            params={
                "productid": product_id,
                "variantId": variant_id,
                "countrycode": (
                    destination_country.upper()
                ),
            },
        )
        if not isinstance(data, dict):
            return []

        variants = data.get("variantlist")
        if not isinstance(variants, list):
            return []

        rates = []
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            logistics_lists = variant.get(
                "logistics_cost_list"
            )
            if not isinstance(logistics_lists, list):
                continue
            for logistics in logistics_lists:
                if not isinstance(logistics, dict):
                    continue
                cost_list = logistics.get("cost_list")
                if isinstance(cost_list, list):
                    rates.extend(cost_list)
        return rates
