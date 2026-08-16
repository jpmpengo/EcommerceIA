from django.test import SimpleTestCase

from product_intelligence.services.ebay_auth_client import (
    EbayAuthClient,
)


class FakeResponse:

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "access_token": "fake-ebay-access-token",
            "expires_in": 7200,
            "token_type": "Application Access Token",
        }


class FakeHttpClient:

    def __init__(self):
        self.last_url = None
        self.last_data = None
        self.last_headers = None
        self.last_auth = None

    def post(
        self,
        url,
        data=None,
        headers=None,
        auth=None,
    ):
        self.last_url = url
        self.last_data = data
        self.last_headers = headers
        self.last_auth = auth

        return FakeResponse()


class EbayAuthClientTests(SimpleTestCase):

    def test_get_access_token(self):
        http_client = FakeHttpClient()

        client = EbayAuthClient(
            client_id="fake-client-id",
            client_secret="fake-client-secret",
            http_client=http_client,
        )

        token = client.get_access_token()

        self.assertEqual(
            http_client.last_url,
            (
                "https://api.ebay.com/"
                "identity/v1/oauth2/token"
            ),
        )

        self.assertEqual(
            http_client.last_data["grant_type"],
            "client_credentials",
        )

        self.assertEqual(
            http_client.last_data["scope"],
            (
                "https://api.ebay.com/oauth/"
                "api_scope"
            ),
        )

        self.assertEqual(
            http_client.last_auth,
            (
                "fake-client-id",
                "fake-client-secret",
            ),
        )

        self.assertEqual(
            token,
            "fake-ebay-access-token",
        )

    def test_get_access_token_fails_when_token_missing(self):
        class FakeResponseWithoutToken:

            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "expires_in": 7200,
                }

        class FakeHttpClientWithoutToken:

            def post(
                self,
                url,
                data=None,
                headers=None,
                auth=None,
            ):
                return FakeResponseWithoutToken()

        client = EbayAuthClient(
            client_id="fake-client-id",
            client_secret="fake-client-secret",
            http_client=FakeHttpClientWithoutToken(),
        )

        with self.assertRaises(
            ValueError,
        ):
            client.get_access_token()

            