from requests.auth import HTTPBasicAuth


class DropXLClient:
    SANDBOX_BASE_URL = "https://sandbox.b2b.dropxl.com"
    PRODUCTION_BASE_URL = "https://b2b.dropxl.com"

    def __init__(self, api_email, api_token, sandbox_mode=True, http_client=None):
        if http_client is None:
            import requests
            http_client = requests
        self.http_client = http_client
        self.auth = HTTPBasicAuth(api_email, api_token)
        self.base_url = self.SANDBOX_BASE_URL if sandbox_mode else self.PRODUCTION_BASE_URL

    def get_products(self, limit=100, offset=0):
        response = self.http_client.get(self.base_url + "/api_customer/products", params={"limit": limit, "offset": offset}, auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()["data"]
