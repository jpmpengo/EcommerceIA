from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from product_intelligence.models import ProductOpportunity
from product_intelligence.services.opportunity_review import (
    OpportunityReviewService,
)


class OpportunityReviewServiceTests(TestCase):

    def test_approves_opportunity_in_review(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            demand_score=80,
            competition_score=50,
            status="review",
            market_collection_batch_id=uuid4(),
        )

        service = OpportunityReviewService()

        result = service.approve(
            opportunity
        )

        self.assertEqual(
            result.status,
            "approved",
        )

        result.refresh_from_db()

        self.assertEqual(
            result.status,
            "approved",
        )

    def test_cannot_approve_when_market_analysis_is_incomplete(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            demand_score=0,
            competition_score=50,
            status="review",
            market_collection_batch_id=uuid4(),
        )

        service = OpportunityReviewService()

        with self.assertRaisesMessage(
            ValueError,
            "demande et de concurrence",
        ):
            service.approve(opportunity)

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "review")

    def test_cannot_approve_without_market_collection_batch_id(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="review",
        )

        service = OpportunityReviewService()

        with self.assertRaisesMessage(
            ValueError,
            "lot de prix comparables",
        ):
            service.approve(opportunity)

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, "review")

    def test_rejects_opportunity_in_review(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="review",
        )

        service = OpportunityReviewService()

        result = service.reject(
            opportunity
        )

        self.assertEqual(
            result.status,
            "rejected",
        )

        result.refresh_from_db()

        self.assertEqual(
            result.status,
            "rejected",
        )

    def test_cannot_approve_opportunity_not_in_review(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="detected",
        )

        service = OpportunityReviewService()

        with self.assertRaisesMessage(
            ValueError,
            "Only opportunities in review can be approved.",
        ):
            service.approve(
                opportunity
            )

        opportunity.refresh_from_db()

        self.assertEqual(
            opportunity.status,
            "detected",
        )

    def test_cannot_reject_opportunity_not_in_review(self):
        opportunity = ProductOpportunity.objects.create(
            name="Wireless Charger",
            source_name="CJdropshipping",
            source_url="https://example.com/product",
            supplier_price=Decimal("4.53"),
            market_price=Decimal("27.90"),
            status="detected",
        )

        service = OpportunityReviewService()

        with self.assertRaisesMessage(
            ValueError,
            "Only opportunities in review can be rejected.",
        ):
            service.reject(
                opportunity
            )

        opportunity.refresh_from_db()

        self.assertEqual(
            opportunity.status,
            "detected",
        )

