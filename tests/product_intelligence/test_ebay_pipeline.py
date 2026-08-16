from django.test import TestCase

from product_intelligence.models import (
    MarketObservation,
    MarketObservationSnapshot,
)
from product_intelligence.services.collectors.ebay import (
    EbayCollector,
)
from product_intelligence.services.ebay_client import (
    EbayClient,
)
from product_intelligence.services.market_observation_importer import (
    MarketObservationImporter,
)

from product_intelligence.services.market_signal_service import (
    MarketSignalService,
)

from product_intelligence.services.opportunity_score_service import (
    OpportunityScoreService,
)

from product_intelligence.services.ai_recommendation_engine import (
    AIRecommendationEngine,
)
from product_intelligence.services.opportunity_recommendation_service import (
    OpportunityRecommendationService,
)



class FakeResponse:

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeHttpClient:

    def get(
        self,
        url,
        params=None,
        headers=None,
    ):
        return FakeResponse(
            {
                "itemSummaries": [
                    {
                        "itemId": "EBAY-REAL-001",
                        "title": (
                            "Support ordinateur portable"
                        ),
                        "price": {
                            "value": "19.90",
                            "currency": "EUR",
                        },
                        "itemWebUrl": (
                            "https://www.ebay.fr/itm/"
                            "EBAY-REAL-001"
                        ),
                        "image": {
                            "imageUrl": (
                                "https://example.com/"
                                "support.jpg"
                            ),
                        },
                    }
                ]
            }
        )

class FakeAIClient:

    def generate(
        self,
        instructions,
        context,
    ):
        return {
            "decision": "study",
            "summary": (
                "Opportunité à étudier "
                "avant sourcing fournisseur."
            ),
        }



class EbayPipelineTests(TestCase):

    def test_ebay_pipeline_imports_observation(self):
        http_client = FakeHttpClient()

        ebay_client = EbayClient(
            access_token="fake-access-token",
            http_client=http_client,
            marketplace_id="EBAY_FR",
        )

        collector = EbayCollector(
            client=ebay_client,
        )

        importer = MarketObservationImporter(
            collector=collector,
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
            "EBAY-REAL-001",
        )

        self.assertEqual(
            str(observation.observed_price),
            "19.90",
        )

        self.assertEqual(
            observation.currency,
            "EUR",
        )

        self.assertEqual(
            MarketObservationSnapshot.objects.count(),
            1,
        )

    def test_ebay_pipeline_tracks_price_change(self):
        class ChangingPriceHttpClient:

            def __init__(self):
                self.price = "19.90"

            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                return FakeResponse(
                    {
                        "itemSummaries": [
                            {
                                "itemId": "EBAY-PRICE-001",
                                "title": (
                                    "Support ordinateur portable"
                                ),
                                "price": {
                                    "value": self.price,
                                    "currency": "EUR",
                                },
                                "itemWebUrl": (
                                    "https://www.ebay.fr/itm/"
                                    "EBAY-PRICE-001"
                                ),
                                "image": {
                                    "imageUrl": (
                                        "https://example.com/"
                                        "support.jpg"
                                    ),
                                },
                            }
                        ]
                    }
                )

        http_client = ChangingPriceHttpClient()

        ebay_client = EbayClient(
            access_token="fake-access-token",
            http_client=http_client,
            marketplace_id="EBAY_FR",
        )

        collector = EbayCollector(
            client=ebay_client,
        )

        importer = MarketObservationImporter(
            collector=collector,
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        http_client.price = "17.50"

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

        observation = MarketObservation.objects.get()

        self.assertEqual(
            str(observation.observed_price),
            "17.50",
        )
        
        snapshots = list(
            MarketObservationSnapshot.objects.order_by(
                "observed_at"
            )
        )

        self.assertEqual(
            str(snapshots[0].observed_price),
            "19.90",
        )

        self.assertEqual(
            str(snapshots[1].observed_price),
            "17.50",
        )
    
    def test_ebay_pipeline_generates_price_signal(self):
        class ChangingPriceHttpClient:

            def __init__(self):
                self.price = "19.90"

            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                return FakeResponse(
                    {
                        "itemSummaries": [
                            {
                                "itemId": "EBAY-SIGNAL-001",
                                "title": (
                                    "Support ordinateur portable"
                                ),
                                "price": {
                                    "value": self.price,
                                    "currency": "EUR",
                                },
                                "itemWebUrl": (
                                    "https://www.ebay.fr/itm/"
                                    "EBAY-SIGNAL-001"
                                ),
                                "image": {
                                    "imageUrl": (
                                        "https://example.com/"
                                        "support.jpg"
                                    ),
                                },
                            }
                        ]
                    }
                )

        http_client = ChangingPriceHttpClient()

        ebay_client = EbayClient(
            access_token="fake-access-token",
            http_client=http_client,
            marketplace_id="EBAY_FR",
        )

        collector = EbayCollector(
            client=ebay_client,
        )

        importer = MarketObservationImporter(
            collector=collector,
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        http_client.price = "17.50"

        importer.import_query(
            query="support ordinateur portable"
        )

        observation = MarketObservation.objects.get()

        signals = MarketSignalService.analyze(
            observation
        )

        self.assertEqual(
            str(signals["previous_price"]),
            "19.90",
        )

        self.assertEqual(
            str(signals["current_price"]),
            "17.50",
        )

        self.assertEqual(
            str(signals["price_change"]),
            "-2.40",
        )

        self.assertEqual(
            str(signals["price_change_percent"]),
            "-12.06",
        )

        self.assertEqual(
            signals["direction"],
            "down",
        )
    
    def test_ebay_pipeline_generates_opportunity_score(self):
        class ChangingPriceHttpClient:

            def __init__(self):
                self.price = "19.90"

            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                return FakeResponse(
                    {
                        "itemSummaries": [
                            {
                                "itemId": "EBAY-SCORE-001",
                                "title": (
                                    "Support ordinateur portable"
                                ),
                                "price": {
                                    "value": self.price,
                                    "currency": "EUR",
                                },
                                "itemWebUrl": (
                                    "https://www.ebay.fr/itm/"
                                    "EBAY-SCORE-001"
                                ),
                                "image": {
                                    "imageUrl": (
                                        "https://example.com/"
                                        "support.jpg"
                                    ),
                                },
                            }
                        ]
                    }
                )

        http_client = ChangingPriceHttpClient()

        ebay_client = EbayClient(
            access_token="fake-access-token",
            http_client=http_client,
            marketplace_id="EBAY_FR",
        )

        collector = EbayCollector(
            client=ebay_client,
        )

        importer = MarketObservationImporter(
            collector=collector,
        )

        importer.import_query(
            query="support ordinateur portable"
        )

        http_client.price = "17.50"

        importer.import_query(
            query="support ordinateur portable"
        )

        observation = MarketObservation.objects.get()

        signals = MarketSignalService.analyze(
            observation
        )

        score_data = OpportunityScoreService.explain(
            signals
        )

        self.assertEqual(
            str(score_data["score"]),
            "62.06",
        )

        self.assertIn(
            "Baisse de prix de 12.06 %",
            score_data["reasons"],
        )

    def test_ebay_pipeline_generates_ai_recommendation(self):
        class ChangingPriceHttpClient:

            def __init__(self):
                self.price = "19.90"

            def get(
                self,
                url,
                params=None,
                headers=None,
            ):
                return FakeResponse(
                    {
                        "itemSummaries": [
                            {
                                "itemId": "EBAY-AI-001",
                                "title": (
                                    "Support ordinateur portable"
                                ),
                                "price": {
                                    "value": self.price,
                                    "currency": "EUR",
                                },
                                "itemWebUrl": (
                                    "https://www.ebay.fr/itm/"
                                    "EBAY-AI-001"
                                ),
                                "image": {
                                    "imageUrl": (
                                        "https://example.com/"
                                        "support.jpg"
                                    ),
                                },
                            }
                        ]
                    }
                )

        http_client = ChangingPriceHttpClient()

        ebay_client = EbayClient(
            access_token="fake-access-token",
            http_client=http_client,
            marketplace_id="EBAY_FR",
        )

        collector = EbayCollector(
            client=ebay_client,
        )

        importer = MarketObservationImporter(
            collector=collector,
        )   

        importer.import_query(
            query="support ordinateur portable"
        )

        http_client.price = "17.50"

        importer.import_query(
            query="support ordinateur portable"
        )

        observation = MarketObservation.objects.get()

        signals = MarketSignalService.analyze(
            observation
        )

        score_data = OpportunityScoreService.explain(
            signals
        )

        ai_client = FakeAIClient()

        engine = AIRecommendationEngine(
            client=ai_client
        )

        service = OpportunityRecommendationService(
            engine=engine
        )

        product_data = {
            "name": observation.name,
            "current_price": observation.observed_price,
            "currency": observation.currency,
        }

        result = service.recommend(
            product_data=product_data,
            score_data=score_data,
        )

        self.assertEqual(
            result["decision"],
            "study",
        )

        self.assertEqual(
            result["summary"],
            (
                "Opportunité à étudier "
                "avant sourcing fournisseur."
            ),
        ) 