from unittest.mock import (
    Mock,
    patch,
)

from django.test import TestCase

from product_intelligence.services.supplier_search_factory import (
    SupplierSearchFactory,
)


class SupplierSearchFactoryTests(TestCase):

    @patch(
        (
            "product_intelligence.services."
            "supplier_search_factory."
            "CJAuthClient"
        )
    )
    def test_builds_configured_cj_and_printful_searchers(
        self,
        auth_client_class,
    ):
        http_client = Mock()

        auth_client_class.return_value.get_access_token.return_value = (
            "cj-access-token"
        )

        searchers = SupplierSearchFactory.build(
            http_client=http_client,
            cj_api_key="cj-api-key",
            printful_api_token=(
                "printful-api-token"
            ),
        )

        self.assertEqual(
            len(searchers),
            2,
        )

        self.assertEqual(
            [
                searcher.supplier.name
                for searcher in searchers
            ],
            [
                "CJdropshipping",
                "Printful",
            ],
        )

        self.assertEqual(
            [
                searcher.max_offers
                for searcher in searchers
            ],
            [
                5,
                5,
            ],
        )

        auth_client_class.assert_called_once_with(
            api_key="cj-api-key",
            http_client=http_client,
        )

        self.assertEqual(
            searchers[0].client.access_token,
            "cj-access-token",
        )

        self.assertEqual(
            searchers[1].client.api_token,
            "printful-api-token",
        )

    @patch(
        (
            "product_intelligence.services."
            "supplier_search_factory."
            "CJAuthClient"
        )
    )
    def test_builds_only_available_supplier(
        self,
        auth_client_class,
    ):
        searchers = SupplierSearchFactory.build(
            http_client=Mock(),
            cj_api_key="",
            printful_api_token=(
                "printful-api-token"
            ),
        )

        self.assertEqual(
            len(searchers),
            1,
        )

        self.assertEqual(
            searchers[0].supplier.name,
            "Printful",
        )

        auth_client_class.assert_not_called()