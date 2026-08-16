from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from product_intelligence.models import ProductOpportunity
from recommendations.services.decision_service import (
    RecommendationDecisionService,
)


class RecommendationDecisionServiceTests(TestCase):
    def setUp(self):
        self.opportunity = ProductOpportunity.objects.create(
            name="Produit test report",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Produit utilisé pour tester le report.",
            initial_stock=5,
        )

    def test_postpone_sets_future_date_without_publishing(self):
        before = timezone.now()

        result = RecommendationDecisionService.postpone(
            self.opportunity
        )

        result.refresh_from_db()

        self.assertIsNotNone(
            result.postponed_until,
        )

        self.assertGreater(
            result.postponed_until,
            before,
        )

        self.assertEqual(
            result.status,
            "approved",
        )

        self.assertIsNone(
            result.published_product,
        )

        