from product_intelligence.services.product_idea_manual_analysis import ProductIdeaManualAnalysisService
from product_intelligence.services.opportunity_commercial_score import OpportunityCommercialScoreService
from product_intelligence.services.comparable_price_summary import ComparablePriceSummaryService
from product_intelligence.services.opportunity_commercial_recalculation import OpportunityCommercialRecalculationService


class OpportunityCompetitionStudyCompletionService:
    @classmethod
    def run(cls, opportunity):
        if opportunity.status != "review":
            return {"status": "skipped"}
        idea = opportunity.supplier_offer.product_idea
        result = ProductIdeaManualAnalysisService.build_saturation_service().search(product_name=idea.name, product_attributes={"customer_problem": idea.customer_problem, "target_customer": idea.target_customer, "countries": idea.countries})
        if result.get("all_urls_invalid"):
            opportunity.status = "rejected"
            opportunity.saturation_level = "indeterminate"
            opportunity.opportunity_score = None
            opportunity.saturation_evidence = {**result, "validation_reason": "Aucune preuve concurrentielle exploitable"}
            opportunity.save(update_fields=["status", "saturation_level", "opportunity_score", "saturation_evidence", "updated_at"])
            return {"status": "rejected", "reason": "Aucune preuve concurrentielle exploitable"}
        if result["level"] == "indeterminate":
            return {"status": "unresolved", "evidence": result, "verification_performed": True}
        opportunity.saturation_level = result["level"]
        summary = ComparablePriceSummaryService.summarize(opportunity.supplier_offer, "EUR")
        pricing = OpportunityCommercialRecalculationService.calculate(opportunity, market_summary=summary)
        if pricing["status"] != "ready":
            return {"status": "unresolved", "reason": pricing.get("reason"), "evidence": result}
        opportunity.saturation_evidence = result
        opportunity.recommended_price = pricing["recommended_price"]
        opportunity.other_costs = pricing["other_costs"]
        opportunity.projected_profit = pricing["projected_profit"]
        opportunity.projected_margin_rate = pricing["projected_margin_rate"]
        opportunity.opportunity_score = pricing["opportunity_score"]
        opportunity.save(update_fields=["saturation_level", "saturation_evidence", "recommended_price", "other_costs", "projected_profit", "projected_margin_rate", "opportunity_score", "updated_at"])
        score = pricing["opportunity_score"]
        return {"status": "updated", "level": result["level"], "opportunity_score": score}
