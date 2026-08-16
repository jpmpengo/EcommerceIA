from django.test import SimpleTestCase

from product_intelligence.services.cj_auth_client import CJAuthClient


class FakeResponse:

    def json(self):
        return {
            "code": 200,
            "result": True,
            "data": {
                "accessToken": "test-access-token",
                "refreshToken": "test-refresh-token",
            },
        }


class FakeHTTPClient:

    def __init__(self):
        self.last_url = None
        self.last_json = None
        self.last_headers = None

    def post(self, url, json=None, headers=None):
        self.last_url = url
        self.last_json = json
        self.last_headers = headers

        return FakeResponse()


class CJAuthClientTests(SimpleTestCase):

    def test_get_access_token_sends_api_key(self):
        http_client = FakeHTTPClient()

        client = CJAuthClient(
            api_key="test-api-key",
            http_client=http_client,
        )

        token = client.get_access_token()

        self.assertEqual(
            http_client.last_url,
            "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken",
        )

        self.assertEqual(
            http_client.last_json,
            {
                "apiKey": "test-api-key",
            },
        )

        self.assertEqual(
            http_client.last_headers,
            {
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(
            token,
            "test-access-token",
        )

    def test_get_access_token_raises_clear_error_when_token_missing(self):
        class MissingTokenResponse:
            def json(self):
                return {
                    "code": 200,
                    "result": True,
                    "data": {},
                }

        class MissingTokenHTTPClient:
            def post(self, url, json=None, headers=None):
                return MissingTokenResponse()

        client = CJAuthClient(
            api_key="test-api-key",
            http_client=MissingTokenHTTPClient(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "CJ access token missing from response.",
        ):
            client.get_access_token()