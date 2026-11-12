from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import ProductOpportunity
from product_intelligence.services.opportunity_decision import (
    OpportunityDecisionService,
)


class OpportunityDecisionServiceTests(TestCase):

    def test_moves_qualified_opportunity_to_review(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("20.00"),
            shipping_cost=Decimal("0.00"),
            demand_score=0,
            competition_score=40,
            opportunity_score=60,
        )

        self.assertEqual(
            opportunity.opportunity_score,
            60,
        )

        service = OpportunityDecisionService(
            minimum_score=60,
        )

        result = service.evaluate(
            opportunity
        )

        self.assertEqual(
            result.status,
            "review",
        )

        result.refresh_from_db()

        self.assertEqual(
            result.status,
            "review",
        )

    def test_keeps_low_score_opportunity_detected(self):
        opportunity = ProductOpportunity.objects.create(
            name="USB Cable",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("12.00"),
            shipping_cost=Decimal("0.00"),
            demand_score=0,
            competition_score=100,
            opportunity_score=0,
        )

        self.assertEqual(
            opportunity.opportunity_score,
            0,
        )

        service = OpportunityDecisionService(
            minimum_score=60,
        )

        result = service.evaluate(
            opportunity
        )

        self.assertEqual(
            result.status,
            "detected",
        )

        result.refresh_from_db()

        self.assertEqual(
            result.status,
            "detected",
        )
    def test_keeps_opportunity_detected_when_commercial_score_is_missing(self):
        opportunity = ProductOpportunity.objects.create(name="Pending Score", source_name="CJdropshipping", supplier_price=Decimal("10.00"), market_price=Decimal("20.00"), shipping_cost=Decimal("0.00"))
        self.assertIsNone(opportunity.opportunity_score)
        result = OpportunityDecisionService(minimum_score=60).evaluate(opportunity)
        result.refresh_from_db()
        self.assertEqual(result.status, "detected")
        self.assertIsNone(result.opportunity_score)
