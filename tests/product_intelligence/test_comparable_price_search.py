from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.comparable_price_search import (
    ComparablePriceSearchResponse,
    ComparablePriceSearchService,
)


class FakeComparablePriceClient:

    def __init__(
        self,
    ):
        self.received_instructions = None
        self.received_context = None
        self.received_response_model = None
        self.received_use_web_search = None

    def generate(
        self,
        instructions,
        context,
        response_model,
        use_web_search=False,
    ):
        self.received_instructions = (
            instructions
        )
        self.received_context = context
        self.received_response_model = (
            response_model
        )
        self.received_use_web_search = (
            use_web_search
        )

        return {
            "comparables": [],
        }


class ComparablePriceSearchServiceTests(
    SimpleTestCase
):

    def test_searches_up_to_five_sourced_comparable_prices(
        self,
    ):
        client = FakeComparablePriceClient()

        offer = Mock()
        offer.product_name = (
            "Stackable Storage Box"
        )
        offer.variant_features = {
            "color": "White",
        }
        offer.product_idea.name = (
            "Rangements modulaires "
            "pour petits logements"
        )
        offer.product_idea.countries = [
            "FR",
            "BE",
            "ES",
        ]

        service = (
            ComparablePriceSearchService(
                client=client,
            )
        )

        result = service.search(
            supplier_offer=offer,
        )

        self.assertEqual(
            result,
            {
                "comparables": [],
            },
        )

        self.assertTrue(
            client.received_use_web_search
        )

        self.assertEqual(
            client.received_response_model,
            ComparablePriceSearchResponse,
        )

        self.assertEqual(
            client.received_context[
                "maximum_comparable_prices"
            ],
            5,
        )

        self.assertEqual(
            client.received_context[
                "supplier_product"
            ]["name"],
            "Stackable Storage Box",
        )

        self.assertIn(
            "sources",
            client.received_instructions,
        )