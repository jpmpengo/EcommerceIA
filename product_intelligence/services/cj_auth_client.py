class CJAuthClient:
    BASE_URL = "https://developers.cjdropshipping.com"

    def __init__(self, api_key, http_client):
        self.api_key = api_key
        self.http_client = http_client

    def get_access_token(self):
        url = (
            f"{self.BASE_URL}"
            "/api2.0/v1/authentication/getAccessToken"
        )

        for attempt in range(2):
            response = self.http_client.post(
                url,
                json={
                    "apiKey": self.api_key,
                },
                headers={
                    "Content-Type": "application/json",
                },
            )

            data = response.json() or {}
            token = (
                (data.get("data") or {})
                .get("accessToken")
            )

            if token:
                return token

        raise ValueError(
            "CJ access token missing from response."
        )


