from django.test import SimpleTestCase

from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)


class FakeCollector(BaseMarketCollector):

    source_name = "fake"

    def collect(self, query):
        return [
            {
                "source": self.source_name,
                "external_id": "ABC123",
                "name": "Support ordinateur portable",
                "description": "Support réglable.",
                "observed_price": "19.90",
                "currency": "EUR",
                "product_url": "https://example.com/ABC123",
                "image_url": "https://example.com/image.jpg",
                "raw_data": {},
            }
        ]


class BaseMarketCollectorTests(SimpleTestCase):

    def test_collector_returns_normalized_observations(self):
        collector = FakeCollector()

        results = collector.collect(
            query="support ordinateur portable"
        )

        self.assertEqual(
            len(results),
            1,
        )

        observation = results[0]

        self.assertEqual(
            observation["source"],
            "fake",
        )

        self.assertEqual(
            observation["external_id"],
            "ABC123",
        )

        self.assertEqual(
            observation["name"],
            "Support ordinateur portable",
        )

        self.assertIn(
            "observed_price",
            observation,
        )

        self.assertIn(
            "raw_data",
            observation,
        )

    def test_invalid_observation_is_rejected(self):
        collector = FakeCollector()

        invalid_observation = {
            "source": "fake",
            "external_id": "ABC123",
            # "name" manque volontairement
            "observed_price": "19.90",
            "currency": "EUR",
            "product_url": "https://example.com/ABC123",
            "image_url": "",
            "raw_data": {},
        }

        with self.assertRaises(ValueError):
            collector.validate_observation(
                invalid_observation
            )

        