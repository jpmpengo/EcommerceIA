
class EbayClient:

    SEARCH_URL = (
        "https://api.ebay.com/"
        "buy/browse/v1/item_summary/search"
    )

    def __init__(
        self,
        access_token,
        http_client,
        marketplace_id="EBAY_FR",
    ):
        self.access_token = access_token
        self.http_client = http_client
        self.marketplace_id = marketplace_id

    def search(
        self,
        query,
    ):
        response = self.http_client.get(
            self.SEARCH_URL,
            params={
                "q": query,
            },
            headers={
                "Authorization": (
                    f"Bearer {self.access_token}"
                ),
                "Accept": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": (
                    self.marketplace_id
                ),
            },
        )

        response.raise_for_status()

        return response.json()

        