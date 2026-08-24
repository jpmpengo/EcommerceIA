from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    MarketObservationSnapshot,
)

from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)

from product_intelligence.services.market_observation_importer import (
    MarketObservationImporter,
)

from product_intelligence.models import (
    MarketplaceStudy,
    ProductIdea,
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
                "raw_data": {
                    "query": query,
                },
            }
        ]


class UpdatingFakeCollector(BaseMarketCollector):
    source_name = "fake"

    def __init__(self):
        self.price = "19.90"

    def collect(self, query):
        return [
            {
                "source": self.source_name,
                "external_id": "ABC123",
                "name": "Support ordinateur portable",
                "description": "Support réglable.",
                "observed_price": self.price,
                "currency": "EUR",
                "product_url": "https://example.com/ABC123",
                "image_url": "https://example.com/image.jpg",
                "raw_data": {
                    "query": query,
                },
            }
        ]


class MarketObservationImporterTests(TestCase):

    def test_importer_creates_observation_without_duplicate(self):
        collector = FakeCollector()

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
            "fake",
        )

        self.assertEqual(
            observation.external_id,
            "ABC123",
        )

        self.assertEqual(
            observation.name,
            "Support ordinateur portable",
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        self.assertEqual(
            MarketObservation.objects.count(),
            1,
        )

    def test_importer_updates_existing_observation(self):
        collector = UpdatingFakeCollector()

        importer = MarketObservationImporter(
            collector=collector
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        observation = MarketObservation.objects.get()

        self.assertEqual(
            str(observation.observed_price),
            "19.90",
        )

        collector.price = "17.50"

        importer.import_query(
            query="support ordinateur portable"
        )

        self.assertEqual(
            MarketObservation.objects.count(),
            1,
        )

        observation.refresh_from_db()

        self.assertEqual(
            str(observation.observed_price),
            "17.50",
        )

    def test_importer_creates_snapshot_for_each_import(self):
        collector = UpdatingFakeCollector()

        importer = MarketObservationImporter(
            collector=collector
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        self.assertEqual(
            MarketObservationSnapshot.objects.count(),
            1,
        )

        first_snapshot = (
            MarketObservationSnapshot.objects.first()
        )

        self.assertEqual(
            str(first_snapshot.observed_price),
            "19.90",
        )

        collector.price = "17.50"

        importer.import_query(
            query="support ordinateur portable"
        )

        self.assertEqual(
            MarketObservation.objects.count(),
            1,
        )

        self.assertEqual(
            MarketObservationSnapshot.objects.count(),
            2,
        )

        prices = list(
            MarketObservationSnapshot.objects
            .order_by("observed_at")
            .values_list(
                "observed_price",
                flat=True,
            )
        )

        self.assertEqual(
            [str(price) for price in prices],
            [
                "19.90",
                "17.50",
            ],
        )

    def test_importer_links_observation_to_marketplace_study(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
            ],
            status="selected",
        )

        study = MarketplaceStudy.objects.create(
            product_idea=idea,
            marketplaces=[
                "fake",
            ],
            queries=[
                "organisateur sous évier",
            ],
            status="draft",
        )

        importer = MarketObservationImporter(
            collector=FakeCollector()
        )

        importer.import_query(
            query="organisateur sous évier",
            study=study,
        )

        observation = MarketObservation.objects.get()

        self.assertIn(
            observation,
            study.observations.all(),
        )

        self.assertEqual(
            observation.raw_data["query"],
            "organisateur sous évier",
        )
        