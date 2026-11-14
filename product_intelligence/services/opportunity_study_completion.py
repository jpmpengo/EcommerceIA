from product_intelligence.services.opportunity_ai_recommendation_runner import OpportunityAIRecommendationRunner

class OpportunityStudyCompletionService:
    @classmethod
    def run(cls, opportunity, recommendation):
        blockers = [b for b in (recommendation.study_blockers or []) if isinstance(b, dict)] if recommendation.decision == "study" else []
        if blockers:
            completion_results = {}
            for entry in reversed(recommendation.completion_history or []):
                if entry.get("requested_complements") == blockers:
                    completion_results = dict(entry.get("results") or {})
                    break
            if completion_results:
                if all(isinstance(result, dict) and result.get("status") in ("integrated", "updated", "verified") for result in completion_results.values()):
                    return {"status": "already_completed", "results": completion_results}
                from datetime import datetime, timedelta
                from django.utils import timezone
                for entry in reversed(recommendation.completion_history or []):
                    if entry.get("requested_complements") == blockers and entry.get("results"):
                        try:
                            last_attempt = datetime.fromisoformat(entry["date"])
                            if timezone.is_naive(last_attempt):
                                last_attempt = timezone.make_aware(last_attempt)
                            if timezone.now() - last_attempt < timedelta(days=7):
                                return {"status": "retry_deferred", "results": completion_results}
                        except (KeyError, ValueError, TypeError):
                            pass
                        break
            updated = False
            comparable_blockers = [b for b in blockers if b.get("category") == "comparable_prices"]
            if comparable_blockers and opportunity.supplier_offer_id:
                from product_intelligence.services.comparable_price_study_completion import ComparablePriceStudyCompletionService
                completion = ComparablePriceStudyCompletionService.run(opportunity.supplier_offer, comparable_blockers)
                completion_results["comparable_prices"] = completion
                updated = completion["status"] == "integrated"
            if any(b.get("category") == "competition" for b in blockers) and opportunity.supplier_offer_id:
                from product_intelligence.services.opportunity_competition_study_completion import OpportunityCompetitionStudyCompletionService
                competition = OpportunityCompetitionStudyCompletionService.run(opportunity)
                completion_results["competition"] = competition
                updated = updated or competition["status"] == "updated"
            if any(b.get("category") == "demand" for b in blockers) and opportunity.supplier_offer_id:
                from product_intelligence.services.opportunity_demand_study_completion import OpportunityDemandStudyCompletionService
                demand = OpportunityDemandStudyCompletionService.run(opportunity)
                completion_results["demand"] = demand
                updated = updated or demand["status"] == "verified"
            if any(b.get("category") == "logistics" for b in blockers) and opportunity.supplier_offer_id:
                from product_intelligence.services.comparable_price_logistics_completion import ComparablePriceLogisticsCompletionService
                logistics = ComparablePriceLogisticsCompletionService.run(opportunity.supplier_offer, destination_country="FR")
                completion_results["logistics"] = logistics
                updated = updated or logistics["status"] == "updated"
            if completion_results:
                from django.utils import timezone
                history = list(recommendation.completion_history or [])
                history.append({"date": timezone.now().isoformat(), "requested_complements": blockers, "results": completion_results})
                recommendation.completion_history = history
                recommendation.save(update_fields=["completion_history"])
                from product_intelligence.services.opportunity_review_context import OpportunityReviewContext
                review_context = OpportunityReviewContext.build(completed_studies={"financial": {"status": "previously_calculated", "rule": "Reuse EcommerceIA financial calculations; reopen only for a new verifiable contradiction"}}, requested_complements=blockers, completion_results=completion_results)
                if updated:
                    OpportunityAIRecommendationRunner.run_with_openai(opportunity, review_context=review_context)
