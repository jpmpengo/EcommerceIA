from django.test import TestCase

from product_intelligence.models import (
    MarketplaceStudy,
    MarketObservation,
    ProductIdea,
)
from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)
from product_intelligence.services.marketplace_study_execution import (
    MarketplaceStudyExecutionService,
)


class LimitedFakeCollector(BaseMarketCollector):

    source_name = "fake"

    def __init__(self):
        self.received_queries = []

    def collect(self, query):
        self.received_queries.append(
            query
        )

        return [
            {
                "source": "fake",
                "external_id": f"FAKE-{number}",
                "name": f"Produit {number}",
                "description": "Produit simulé.",
                "observed_price": "19.90",
                "currency": "EUR",
                "product_url": (
                    "https://example.com/"
                    f"products/{number}"
                ),
                "image_url": (
                    "https://example.com/"
                    f"images/{number}.jpg"
                ),
                "raw_data": {
                    "query": query,
                },
            }
            for number in range(5)
        ]


class MarketplaceStudyExecutionServiceTests(
    TestCase
):

    def test_execute_imports_only_configured_result_limit(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
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
            max_pages_per_marketplace=1,
            max_results_per_query=2,
            status="draft",
        )

        collector = LimitedFakeCollector()

        service = (
            MarketplaceStudyExecutionService(
                collectors={
                    "fake": collector,
                }
            )
        )

        executed_study = service.execute(
            study
        )

        study.refresh_from_db()

        self.assertEqual(
            executed_study.pk,
            study.pk,
        )

        self.assertEqual(
            study.status,
            "completed",
        )

        self.assertEqual(
            collector.received_queries,
            [
                "organisateur sous évier",
            ],
        )

        self.assertEqual(
            MarketObservation.objects.count(),
            2,
        )

        self.assertEqual(
            study.observations.count(),
            2,
        )