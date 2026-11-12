from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from dashboard.models import EmmaMemory
from dashboard.services.emma_briefing_service import EmmaBriefingService
from product_intelligence.models import ProductOpportunity, OpportunityAIRecommendation


User = get_user_model()


class EmmaBriefingServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="commercant",
            password="mot-de-passe-test",
        )

    def test_build_returns_briefing_focused_on_review_opportunities(self):
        review = ProductOpportunity.objects.create(
            name="Opportunite a examiner",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            status="review",
        )
        ProductOpportunity.objects.create(
            name="Opportunite encore detectee",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            status="detected",
        )
        ProductOpportunity.objects.create(
            name="Opportunite deja approuvee",
            source_name="Test",
            supplier_price=Decimal("10.00"),
            market_price=Decimal("30.00"),
            status="approved",
        )

        OpportunityAIRecommendation.objects.create(opportunity=review, decision="recommend", summary="Etude terminee")
        briefing = EmmaBriefingService.build(self.user)

        self.assertEqual(list(briefing["opportunities"]), [review])
        self.assertIn("greeting", briefing)
        self.assertIn("summary", briefing)
        self.assertIn("changes", briefing)

    def test_build_does_not_expose_functions_outside_briefing(self):
        briefing = EmmaBriefingService.build(self.user)

        for key in (
            "progress",
            "priorite",
            "alerts",
            "preparation",
            "restock",
            "activity",
            "next_actions",
        ):
            self.assertNotIn(key, briefing)

    def test_first_visit_returns_bonjour(self):
        briefing = EmmaBriefingService.build(self.user)

        self.assertEqual(briefing["greeting"]["title"], "Bonjour")
        self.assertIsNone(briefing["greeting"]["previous_visit"])

    def test_second_visit_same_day_returns_bon_retour(self):
        EmmaBriefingService.build(self.user)

        briefing = EmmaBriefingService.build(self.user)

        self.assertEqual(briefing["greeting"]["title"], "Bon retour")
        self.assertIsNotNone(briefing["greeting"]["previous_visit"])

    def test_first_visit_of_new_day_returns_bonjour(self):
        EmmaMemory.objects.update_or_create(
            user=self.user,
            defaults={
                "last_visit": timezone.now() - timedelta(days=1),
            },
        )

        briefing = EmmaBriefingService.build(self.user)

        self.assertEqual(briefing["greeting"]["title"], "Bonjour")

    def test_build_orders_scored_opportunities_before_missing_scores(self):
        opportunities = {}
        for score in (None, 0, 80):
            opportunities[score] = ProductOpportunity.objects.create(name=f"Produit {score}", source_name="Test", supplier_price=Decimal("10.00"), market_price=Decimal("30.00"), status="review", opportunity_score=score)
        for score, opportunity in opportunities.items():
            OpportunityAIRecommendation.objects.create(opportunity=opportunity, decision="reject" if score == 0 else "recommend", summary="Etude terminee")
        briefing = EmmaBriefingService.build(self.user)
        self.assertEqual(list(briefing["opportunities"]), [opportunities[80], opportunities[0], opportunities[None]])
