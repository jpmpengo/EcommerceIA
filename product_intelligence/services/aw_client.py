class AWClient:
    DEFAULT_BASE_URL = "https://api.aiku.io"

    def __init__(
        self,
        api_token,
        api_base_url=None,
        http_client=None,
    ):
        self.api_token = api_token
        self.api_base_url = (
            api_base_url or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self.http_client = http_client

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "User-Agent": "EcommerceIA/1.0",
        }

    def search_products(self, keyword):
        response = self.http_client.get(
            f"{self.api_base_url}/dropshipping/products",
            params={
                "search": keyword,
                "include": "department,sub_department,family",
            },
            headers=self._headers(),
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", [])
