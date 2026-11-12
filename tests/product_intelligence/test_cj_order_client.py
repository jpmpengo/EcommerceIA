from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.cj_client import CJClient


class CJOrderClientTests(SimpleTestCase):
    def test_creates_sandbox_order_v3(self):
        response = Mock()
        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {"orderId": "CJ-TEST-1"},
        }
        http_client = Mock()
        http_client.post.return_value = response
        client = CJClient("TOKEN", http_client)

        result = client.create_order_v3({"isSandbox": 1})

        self.assertEqual(result["orderId"], "CJ-TEST-1")
        self.assertTrue(
            http_client.post.call_args.args[0].endswith("/createOrderV3")
        )

    def test_refuses_payload_without_sandbox(self):
        http_client = Mock()
        client = CJClient("TOKEN", http_client)

        with self.assertRaisesMessage(ValueError, "isSandbox=1"):
            client.create_order_v3({"isSandbox": 0})
        http_client.post.assert_not_called()

    def test_sandbox_lifecycle_calls_documented_endpoints(self):
        response = Mock()
        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": True,
        }
        http_client = Mock()
        http_client.post.return_value = response
        http_client.patch.return_value = response
        client = CJClient("TOKEN", http_client)

        self.assertEqual(client.confirm_order("SD-1"), True)
        self.assertTrue(client.sandbox_simulate_pay("SD-1"))
        self.assertTrue(client.sandbox_update_status("SD-1", 400))
        self.assertTrue(client.sandbox_update_track_number("SD-1", "TEST-1"))

        urls = [call.args[0] for call in http_client.post.call_args_list]
        self.assertTrue(
            http_client.patch.call_args.args[0].endswith("/order/confirmOrder")
        )
        self.assertEqual(
            http_client.patch.call_args.kwargs["json"],
            {"orderId": "SD-1"},
        )
        self.assertTrue(urls[0].endswith("/sandbox/simulatePay"))
        self.assertTrue(urls[1].endswith("/sandbox/updateStatus"))
        self.assertTrue(urls[2].endswith("/sandbox/updateTrackNumber"))

    def test_refuses_unsupported_sandbox_status(self):
        http_client = Mock()
        client = CJClient("TOKEN", http_client)

        with self.assertRaisesMessage(ValueError, "Statut sandbox CJ invalide"):
            client.sandbox_update_status("SD-1", 300)
        http_client.post.assert_not_called()

    def test_queries_order_detail(self):
        response = Mock()
        response.json.return_value = {
            "code": 200,
            "result": True,
            "data": {"orderId": "SD-1", "isSandbox": True},
        }
        http_client = Mock()
        http_client.get.return_value = response
        client = CJClient("TOKEN", http_client)

        result = client.get_order_detail("SD-1")

        self.assertTrue(result["isSandbox"])
        self.assertEqual(http_client.get.call_args.kwargs["params"], {"orderId": "SD-1"})
