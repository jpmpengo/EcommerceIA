from django.utils import timezone
from product_intelligence.services.product_idea_generation import ProductIdeaGenerationService
from product_intelligence.services.product_idea_score_service import ProductIdeaScoreService


class OpportunityDemandStudyCompletionService:
    @classmethod
    def run(cls, opportunity):
        if opportunity.status != "review" or not opportunity.supplier_offer_id:
            return {"status": "skipped"}
        idea = opportunity.supplier_offer.product_idea
        if idea is None:
            return {"status": "skipped"}
        signals = list(idea.demand_signal_assessments or [])
        discovered_new = False
        pending = [s for s in signals if s.get("metric") in ("search_trend", "sales_growth") and s.get("is_verified") is not True]
        if not pending:
            from product_intelligence.services.opportunity_demand_evidence_search import OpportunityDemandEvidenceSearchService
            discovered = OpportunityDemandEvidenceSearchService.search(idea)
            pending = [dict(item) for item in discovered if item.get("metric") in ("search_trend", "sales_growth") and item.get("source_url") and item.get("value")]
            if not pending:
                return {"status": "unresolved", "reason": "no_new_growth_evidence", "verification_performed": True}
            discovered_new = True
        checked = ProductIdeaGenerationService._verify_growth_signals(pending)
        verified = 0
        for original, result in zip(pending, checked):
            if result.get("is_verified") is True:
                if discovered_new:
                    signals.append(result)
                else:
                    original["is_verified"] = True
                verified += 1
        if not verified:
            return {"status": "unresolved", "reason": "no_new_verified_evidence", "verification_performed": True}
        idea.demand_signal_assessments = signals
        idea.idea_score = ProductIdeaScoreService.calculate(signals, reference_date=timezone.localdate())
        idea.save(update_fields=["demand_signal_assessments", "idea_score"])
        from product_intelligence.services.demand_score_service import DemandScoreService
        from product_intelligence.services.opportunity_commercial_score import OpportunityCommercialScoreService
        demand_score = DemandScoreService.calculate(signals)
        total_cost = opportunity.supplier_price + opportunity.shipping_cost + opportunity.other_costs
        margin_rate = ((opportunity.market_price - total_cost) / total_cost * 100) if total_cost > 0 else 0
        opportunity.demand_score = demand_score
        opportunity.opportunity_score = OpportunityCommercialScoreService.calculate(margin_rate, demand_score, opportunity.saturation_level)
        opportunity.save(update_fields=["demand_score", "opportunity_score", "updated_at"])
        return {"status": "verified", "verified_count": verified, "demand_score": demand_score, "opportunity_score": opportunity.opportunity_score}
