class EtsyClient:

    BASE_URL = "https://openapi.etsy.com/v3/application"

    def __init__(
        self,
        api_key,
        shared_secret,
        http_client,
    ):
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.http_client = http_client

    def _headers(self):
        return {
            "x-api-key": (
                f"{self.api_key}:{self.shared_secret}"
            ),
        }

    def ping(self):
        url = f"{self.BASE_URL}/openapi-ping"

        response = self.http_client.get(
            url,
            headers=self._headers(),
        )

        response.raise_for_status()

        return response.json()

    def get_listing(
        self,
        listing_id,
    ):
        url = (
            f"{self.BASE_URL}/listings/"
            f"{listing_id}"
        )

        response = self.http_client.get(
            url,
            headers=self._headers(),
        )

        response.raise_for_status()

        return response.json()

    def normalize_listing(self, listing):
        price = listing.get("price") or {}

        amount = price.get("amount")
        divisor = price.get("divisor") or 100

        observed_price = None

        if amount is not None:
            observed_price = f"{amount / divisor:.2f}"

        return {
            "external_id": str(listing["listing_id"]),
            "name": listing.get("title", ""),
            "observed_price": observed_price,
            "currency": price.get("currency_code"),
            "product_url": listing.get("url", ""),
        }

    def search_active_listings(
        self,
        keywords,
        limit=25,
        offset=0,
    ):
        url = (
            f"{self.BASE_URL}/"
            "listings/active"
        )

        response = self.http_client.get(
            url,
            headers=self._headers(),
            params={
                "keywords": keywords,
                "limit": limit,
                "offset": offset,
            },
        )

        response.raise_for_status()

        return response.json()

    
        
        