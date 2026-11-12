from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.supplier_offer_research_pipeline import (
    SupplierOfferResearchPipeline,
)


class SupplierOfferResearchPipelineTests(
    SimpleTestCase
):

    def test_rejects_slow_offer_before_comparable_price_search(
        self,
    ):
        supplier_offer = Mock()

        shipping_service = Mock()
        shipping_service.enrich.return_value = {
            "status": "estimated",
            "cost": "5.06",
            "currency": "USD",
            "shipping_days": 50,
            "shipping_country": "FR",
            "method": "CJPacket Eub",
        }

        delivery_policy = Mock()
        delivery_policy.evaluate.return_value = {
            "status": "rejected",
            "reason": (
                "Délai supérieur à 20 jours."
            ),
            "score_penalty": None,
        }

        comparable_price_collection = Mock()

        pipeline = SupplierOfferResearchPipeline(
            shipping_service=shipping_service,
            delivery_policy=delivery_policy,
            comparable_price_collection=(
                comparable_price_collection
            ),
        )

        result = pipeline.process(
            supplier_offer=supplier_offer,
            destination_country="FR",
        )

        shipping_service.enrich.assert_called_once_with(
            supplier_offer=supplier_offer,
            destination_country="FR",
        )

        delivery_policy.evaluate.assert_called_once_with(
            shipping_days=50,
        )

        comparable_price_collection.collect.assert_not_called()

        self.assertEqual(
            result["status"],
            "rejected",
        )

        self.assertEqual(
            result["comparable_prices_saved"],
            0,
        )

    def test_searches_prices_for_accepted_offer(
        self,
    ):
        supplier_offer = Mock()

        shipping_service = Mock()
        shipping_service.enrich.return_value = {
            "status": "estimated",
            "cost": "3.00",
            "currency": "EUR",
            "shipping_days": 8,
            "shipping_country": "FR",
            "method": "Standard",
        }

        delivery_policy = Mock()
        delivery_policy.evaluate.return_value = {
            "status": "accepted",
            "reason": "",
            "score_penalty": 0,
        }

        comparable_price_collection = Mock()
        comparable_price_collection.collect.return_value = [
            Mock(),
            Mock(),
            Mock(),
        ]

        pipeline = SupplierOfferResearchPipeline(
            shipping_service=shipping_service,
            delivery_policy=delivery_policy,
            comparable_price_collection=(
                comparable_price_collection
            ),
        )

        result = pipeline.process(
            supplier_offer=supplier_offer,
            destination_country="FR",
        )

        comparable_price_collection.collect.assert_called_once_with(
            supplier_offer=supplier_offer,
        )

        self.assertEqual(
            result["status"],
            "researched",
        )

        self.assertEqual(
            result["delivery_status"],
            "accepted",
        )

        self.assertEqual(
            result["comparable_prices_saved"],
            3,
        )

    def test_searches_prices_for_fallback_offer(self):
        supplier_offer = Mock()
        shipping_service = Mock()
        shipping_service.enrich.return_value = {
            "status": "estimated",
            "shipping_days": 50,
        }
        delivery_policy = Mock()
        delivery_policy.evaluate.return_value = {
            "status": "fallback",
            "reason": "Offre de repli.",
            "score_penalty": 15,
        }
        comparable_price_collection = Mock()
        comparable_price_collection.collect.return_value = [
            Mock(),
        ]
        pipeline = SupplierOfferResearchPipeline(
            shipping_service=shipping_service,
            delivery_policy=delivery_policy,
            comparable_price_collection=(
                comparable_price_collection
            ),
        )

        result = pipeline.process(
            supplier_offer=supplier_offer,
            destination_country="FR",
        )

        self.assertEqual(result["status"], "researched")
        self.assertEqual(
            result["delivery_status"],
            "fallback",
        )

    def test_stops_when_shipping_quote_is_unavailable(
        self,
    ):
        supplier_offer = Mock()

        shipping_service = Mock()
        shipping_service.enrich.return_value = {
            "status": "unavailable",
            "reason": (
                "Aucun devis de livraison "
                "disponible."
            ),
        }

        delivery_policy = Mock()
        comparable_price_collection = Mock()

        pipeline = SupplierOfferResearchPipeline(
            shipping_service=shipping_service,
            delivery_policy=delivery_policy,
            comparable_price_collection=(
                comparable_price_collection
            ),
        )

        result = pipeline.process(
            supplier_offer=supplier_offer,
            destination_country="FR",
        )

        delivery_policy.evaluate.assert_not_called()

        comparable_price_collection.collect.assert_not_called()

        self.assertEqual(
            result["status"],
            "incomplete",
        )

        self.assertEqual(
            result["comparable_prices_saved"],
            0,
        )
