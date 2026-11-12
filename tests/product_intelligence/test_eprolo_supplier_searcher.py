from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.eprolo_supplier_searcher import (
    EproloSupplierSearcher,
)


class EproloSupplierSearcherTests(SimpleTestCase):

    def test_passes_supplier_search_keyword_to_offer_service(self):
        idea = Mock()
        idea.name = "Bicycle accessories"
        idea.supplier_search_keywords = [
            "USB rechargeable bike light"
        ]

        client = Mock()
        client.search_products.return_value = [
            {
                "id": "P1",
                "title": "Bike Light",
                "variantlist": [
                    {
                        "id": "V1",
                        "title": "Black",
                        "cost": "3.94",
                    }
                ],
            }
        ]

        category_resolver = Mock()
        category_resolver.resolve.return_value = {
            "category_id": "C1"
        }

        offer_service = Mock()
        offer_service.create_offer_from_variant.return_value = Mock()

        searcher = EproloSupplierSearcher(
            client=client,
            supplier=Mock(),
            offer_service=offer_service,
            matching_service=Mock(),
            category_resolver=category_resolver,
            max_offers=5,
        )

        searcher.search_for_idea(
            product_idea=idea,
        )

        self.assertEqual(
            offer_service.create_offer_from_variant.call_args.kwargs[
                "supplier_search_keyword"
            ],
            "USB rechargeable bike light",
        )
