import hashlib
from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.eprolo_client import EproloClient


class EproloClientTests(SimpleTestCase):

    def test_signs_and_reads_global_catalog(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "code": "0",
            "msg": "success",
            "data": [{"id": "32552962"}],
        }
        http_client = Mock()
        http_client.get.return_value = response
        client = EproloClient(
            api_key="key",
            api_secret="secret",
            http_client=http_client,
            timestamp_factory=lambda: 1234567890123,
        )

        result = client.get_catalog_page(page=2)

        expected_sign = hashlib.md5(
            b"key1234567890123secret"
        ).hexdigest()
        self.assertEqual(result, [{"id": "32552962"}])
        http_client.get.assert_called_once_with(
            (
                "https://openapi.eprolo.com/"
                "eprolo_product_list.html"
            ),
            params={
                "page": 2,
                "timestamp": "1234567890123",
                "sign": expected_sign,
            },
            headers={
                "apiKey": "key",
                "ContentType": "application/json",
                "Accept": "application/json",
                "User-Agent": "EcommerceIA/1.0",
            },
        )

    def test_flattens_shipping_rates(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "code": "0",
            "data": {
                "variantlist": [
                    {
                        "logistics_cost_list": [
                            {
                                "cost_list": [
                                    {
                                        "cost": 12.54,
                                        "shiptime": "6-10 Days",
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
        }
        http_client = Mock()
        http_client.get.return_value = response
        client = EproloClient(
            "key", "secret", http_client,
            timestamp_factory=lambda: 1,
        )

        rates = client.get_shipping_rates(
            product_id="10",
            variant_id="20",
            destination_country="fr",
        )

        self.assertEqual(rates[0]["cost"], 12.54)
        params = http_client.get.call_args.kwargs["params"]
        self.assertEqual(params["productid"], "10")
        self.assertEqual(params["variantId"], "20")
        self.assertEqual(params["countrycode"], "FR")

    def test_catalog_search_sends_and_verifies_category(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "code": "0",
            "data": [
                {
                    "id": "1",
                    "title": "Garden hanging planter",
                    "wareTypeId": ",15,",
                    "wareTypeTwoId": ",134,",
                },
                {
                    "id": "2",
                    "title": "Unrelated planter",
                    "wareTypeId": ",15,",
                    "wareTypeTwoId": ",140,",
                },
            ],
        }
        http_client = Mock()
        http_client.get.return_value = response
        matching = Mock()
        matching.is_relevant.return_value = True
        client = EproloClient(
            "key", "secret", http_client,
            timestamp_factory=lambda: 1,
        )

        products = client.search_products(
            keyword="garden planter",
            matching_service=matching,
            ware_type_id=15,
            ware_type_two_id=134,
            max_pages=1,
        )

        self.assertEqual([item["id"] for item in products], ["1"])
        params = http_client.get.call_args.kwargs["params"]
        self.assertEqual(params["wareTypeId"], 15)
        self.assertEqual(params["wareTypeTwoId"], 134)
