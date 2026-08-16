from django.test import SimpleTestCase, TestCase

from product_intelligence.services.collectors.ebay import (
    EbayCollector,
)

from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    MarketObservationSnapshot,
)
from product_intelligence.services.market_observation_importer import (
    MarketObservationImporter,
)




class FakeEbayClient:

    def search(self, query):
        return {
            "itemSummaries": [
                {
                    "itemId": "EBAY123",
                    "title": (
                        "Support ordinateur portable réglable"
                    ),
                    "price": {
                        "value": "17.50",
                        "currency": "EUR",
                    },
                    "itemWebUrl": (
                        "https://www.ebay.fr/itm/EBAY123"
                    ),
                    "image": {
                        "imageUrl": (
                            "https://example.com/support.jpg"
                        ),
                    },
                }
            ]
        }


class EbayCollectorTests(SimpleTestCase):

    def test_collector_normalizes_ebay_item(self):
        client = FakeEbayClient()

        collector = EbayCollector(
            client=client
        )

        results = collector.collect(
            query="support ordinateur portable"
        )

        self.assertEqual(
            len(results),
            1,
        )

        item = results[0]

        self.assertEqual(
            item["source"],
            "ebay",
        )

        self.assertEqual(
            item["external_id"],
            "EBAY123",
        )

        self.assertEqual(
            item["name"],
            "Support ordinateur portable réglable",
        )

        self.assertEqual(
            item["observed_price"],
            "17.50",
        )

        self.assertEqual(
            item["currency"],
            "EUR",
        )

        self.assertEqual(
            item["product_url"],
            "https://www.ebay.fr/itm/EBAY123",
        )

        self.assertEqual(
            item["image_url"],
            "https://example.com/support.jpg",
        )

    def test_collector_results_respect_base_contract(self):
        client = FakeEbayClient()

        collector = EbayCollector(
            client=client
        )

        results = collector.collect(
            query="support ordinateur portable"
        )

        validated_results = collector.validate_results(
            results
        )

        self.assertEqual(
            validated_results,
            results,
        )
    
class EbayCollectorImporterTests(TestCase):

    def test_ebay_result_can_be_imported(self):
        client = FakeEbayClient()

        collector = EbayCollector(
            client=client
        )

        importer = MarketObservationImporter(
            collector=collector
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        self.assertEqual(
            MarketObservation.objects.count(),
            1,
        )

        observation = MarketObservation.objects.get()

        self.assertEqual(
            observation.source,
            "ebay",
        )

        self.assertEqual(
            observation.external_id,
            "EBAY123",
        )

        self.assertEqual(
            observation.name,
            "Support ordinateur portable réglable",
        )

        self.assertEqual(
            str(observation.observed_price),
            "17.50",
        )

        self.assertEqual(
            observation.currency,
            "EUR",
        )

        self.assertEqual(
            MarketObservationSnapshot.objects.count(),
            1,
        )



