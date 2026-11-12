from django.db.models import F
from django.utils import timezone

from dashboard.services.emma_changes_service import EmmaChangesService
from dashboard.services.emma_memory_service import EmmaMemoryService
from dashboard.services.emma_state_service import EmmaStateService
from dashboard.services.emma_summary_service import EmmaSummaryService
from product_intelligence.models import ProductOpportunity
from product_intelligence.services.comparable_price_summary import ComparablePriceSummaryService
from product_intelligence.services.opportunity_commercial_recalculation import OpportunityCommercialRecalculationService
from product_intelligence.services.pricing_policy import get_market_price_reference


class EmmaBriefingService:
    """Prepare le briefing presente par Emma au commercant."""

    @staticmethod
    def build(user):
        previous_visit = EmmaMemoryService.record_visit(user)

        opportunities = (
            ProductOpportunity.objects
            .filter(status="review", ai_recommendation__decision__in=["recommend", "reject"])
            .select_related("supplier_offer", "ai_recommendation")
            .order_by(F("opportunity_score").desc(nulls_last=True), "-detected_at")
        )

        opportunities = list(opportunities)
        for opportunity in opportunities:
            summary = ComparablePriceSummaryService.summarize(opportunity.supplier_offer, "EUR")
            opportunity.market_summary = summary
            opportunity.market_reference_type = get_market_price_reference()
            reference_field = {"minimum": "minimum_price", "median": "commercial_median_price", "maximum": "maximum_price"}[opportunity.market_reference_type]
            opportunity.market_reference_price = summary.get(reference_field)
            opportunity.commercial_pricing = OpportunityCommercialRecalculationService.calculate(opportunity, market_summary=summary)

        state = EmmaStateService.get_state(
            review_opportunities_count=len(opportunities),
        )

        return {
            "greeting": EmmaBriefingService._build_greeting(previous_visit),
            "summary": EmmaSummaryService.build(state),
            "changes": EmmaBriefingService._build_changes(previous_visit),
            "opportunities": opportunities,
        }

    @staticmethod
    def _build_greeting(previous_visit):
        today = timezone.localdate()

        if previous_visit is None:
            return {
                "title": "Bonjour",
                "message": "Voici les opportunites preparees pour votre examen.",
                "previous_visit": None,
            }

        previous_visit_date = timezone.localtime(previous_visit).date()

        if previous_visit_date < today:
            title = "Bonjour"
        else:
            title = "Bon retour"

        return {
            "title": title,
            "message": "Voici les opportunites qui attendent votre examen.",
            "previous_visit": previous_visit,
        }

    @staticmethod
    def _build_changes(previous_visit):
        changes = EmmaChangesService.get_changes(previous_visit)

        if changes:
            return changes

        return [
            {
                "icon": "✨",
                "message": "Aucune nouvelle opportunite depuis votre derniere visite.",
            }
        ]
