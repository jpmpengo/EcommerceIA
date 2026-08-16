class EbayAuthClient:

    TOKEN_URL = (
        "https://api.ebay.com/"
        "identity/v1/oauth2/token"
    )

    SCOPE = (
        "https://api.ebay.com/oauth/"
        "api_scope"
    )

    def __init__(
        self,
        client_id,
        client_secret,
        http_client,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.http_client = http_client

    def get_access_token(self):
        response = self.http_client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "scope": self.SCOPE,
            },
            headers={
                "Content-Type": (
                    "application/x-www-form-urlencoded"
                ),
            },
            auth=(
                self.client_id,
                self.client_secret,
            ),
        )

        response.raise_for_status()

        data = response.json()

        access_token = data.get(
            "access_token"
        )

        if not access_token:
            raise ValueError(
                (
                    "eBay n'a pas retourné "
                    "de jeton d'accès."
                )
            )

        return access_token

        