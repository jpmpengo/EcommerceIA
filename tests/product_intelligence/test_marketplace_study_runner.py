from unittest.mock import patch

from django.test import TestCase

from product_intelligence.models import (
    MarketplaceStudy,
    ProductIdea,
)
from product_intelligence.services.collectors.base import (
    BaseMarketCollector,
)
from product_intelligence.services.marketplace_study_runner import (
    MarketplaceStudyRunner,
)


class RunnerFakeCollector(BaseMarketCollector):

    source_name = "etsy"

    def collect(
        self,
        query,
    ):
        return [
            {
                "source": self.source_name,
                "external_id": "ETSY-001",
                "name": "Organisateur sous évier",
                "description": "Rangement modulable.",
                "observed_price": "29.90",
                "currency": "EUR",
                "product_url": (
                    "https://www.etsy.com/"
                    "listing/ETSY-001"
                ),
                "image_url": "",
                "raw_data": {
                    "query": query,
                },
            }
        ]


class MarketplaceStudyRunnerTests(TestCase):

    @patch(
        (
            "product_intelligence.services."
            "marketplace_study_runner."
            "MarketplaceCollectorFactory.build"
        )
    )
    def test_run_builds_collectors_and_executes_study(
        self,
        mock_build,
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
                "etsy",
            ],
            queries=[
                "organisateur sous évier",
            ],
            max_results_per_query=20,
            status="draft",
        )

        mock_build.return_value = {
            "etsy": RunnerFakeCollector(),
        }

        executed_study = (
            MarketplaceStudyRunner.run(
                study
            )
        )

        study.refresh_from_db()

        mock_build.assert_called_once_with(
            marketplaces=[
                "etsy",
            ],
        )

        self.assertEqual(
            executed_study.pk,
            study.pk,
        )

        self.assertEqual(
            study.status,
            "completed",
        )

        self.assertEqual(
            study.observations.count(),
            1,
        )