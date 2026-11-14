from product_intelligence.models import ProductIdea, ProductOpportunity
from product_intelligence.services.opportunity_ai_recommendation_runner import OpportunityAIRecommendationRunner
from product_intelligence.services.product_idea_manual_analysis import ProductIdeaManualAnalysisService
from product_intelligence.services.product_idea_selection import ProductIdeaSelectionService


class ProductIdeaNightlyOrchestratorService:

    @classmethod
    def get_pending_opportunities(cls):
        return ProductOpportunity.objects.filter(status="review").filter(__import__("django.db.models", fromlist=["Q"]).Q(ai_recommendation__isnull=True) | __import__("django.db.models", fromlist=["Q"]).Q(ai_recommendation__decision="study") | __import__("django.db.models", fromlist=["Q"]).Q(ai_recommendation__decision="recommend", category__isnull=True)).order_by("pk")

    @classmethod
    def retry_pending_opportunities(cls):
        from product_intelligence.services.opportunity_study_completion import OpportunityStudyCompletionService
        results = {"processed": [], "failures": []}
        for opportunity in cls.get_pending_opportunities():
            try:
                recommendation = getattr(opportunity, "ai_recommendation", None)
                if recommendation is None:
                    recommendation = OpportunityAIRecommendationRunner.run_with_openai(opportunity)
                if recommendation.decision == "recommend" and opportunity.category_id is None:
                    from products.services.opportunity_category_assignment import OpportunityCategoryAssignmentService
                    assigned = OpportunityCategoryAssignmentService.assign(opportunity, recommendation.category_path, recommendation.category_reason)
                    if not assigned:
                        raise ValueError("Categorisation automatique impossible pour opportunite recommandee")
                OpportunityStudyCompletionService.run(opportunity, recommendation)
                results["processed"].append(opportunity.pk)
            except Exception as exc:
                results["failures"].append({"opportunity_id": opportunity.pk, "error": str(exc)})
        return results

    @classmethod
    def run(
        cls,
        idea_id=None,
        selection_service=ProductIdeaSelectionService,
        analysis_service=ProductIdeaManualAnalysisService,
    ):
        retry_results = cls.retry_pending_opportunities() if idea_id is None else {"processed": [], "failures": []}

        generated_idea_ids = []
        if idea_id is None and not retry_results["failures"] and not ProductIdea.objects.filter(status__in=["proposed", "selected"]).exists():
            from product_intelligence.services.product_idea_generation import ProductIdeaGenerationService
            existing_idea_ids = set(ProductIdea.objects.values_list("pk", flat=True))
            ProductIdeaGenerationService.generate()
            generated_idea_ids = list(ProductIdea.objects.exclude(pk__in=existing_idea_ids).order_by("pk").values_list("pk", flat=True))

        ideas = ProductIdea.objects.filter(
            status__in=["proposed", "selected"],
        )

        if idea_id is not None:
            ideas = ideas.filter(pk=idea_id)

        ideas = ideas.order_by(
            "-idea_score",
            "created_at",
            "pk",
        )

        succeeded_ids = []
        failed_ids = []
        failures = []
        analysis_reports = []
        recommendation_reports = []

        for idea in ideas:
            try:
                selected_idea = selection_service.select(
                    idea,
                    selection_source="automatic",
                )
            except Exception as exc:
                failed_ids.append(idea.pk)
                failures.append({
                    "product_idea_id": idea.pk,
                    "stage": "selection",
                    "error": str(exc),
                })
                continue

            try:
                analysis_result = analysis_service.run(
                    product_idea=selected_idea,
                )
            except Exception as exc:
                failed_ids.append(selected_idea.pk)
                failures.append({
                    "product_idea_id": selected_idea.pk,
                    "stage": "analysis",
                    "error": str(exc),
                })
                continue

            if isinstance(analysis_result, dict):
                analysis_reports.append(analysis_result)
                for opportunity_id in analysis_result.get("processed_opportunity_ids", []):
                    try:
                        opportunity = ProductOpportunity.objects.get(pk=opportunity_id, status="review")
                        recommendation = OpportunityAIRecommendationRunner.run_with_openai(opportunity)
                        from product_intelligence.services.opportunity_study_completion import OpportunityStudyCompletionService
                        OpportunityStudyCompletionService.run(opportunity, recommendation)
                        recommendation_reports.append({"opportunity_id": opportunity_id, "status": "completed"})
                    except Exception as exc:
                        failures.append({"product_idea_id": selected_idea.pk, "opportunity_id": opportunity_id, "stage": "ai_recommendation", "error": str(exc)})
            succeeded_ids.append(selected_idea.pk)

        return {
            "retry_results": retry_results,
            "succeeded_ids": succeeded_ids,
            "failed_ids": failed_ids,
            "failures": failures,
            "generated_idea_ids": generated_idea_ids,
            "analysis_reports": analysis_reports,
            "recommendation_reports": recommendation_reports,
        }
