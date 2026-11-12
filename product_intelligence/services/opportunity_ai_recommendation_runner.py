from product_intelligence.models import OpportunityAIRecommendation
from product_intelligence.services.advisor import OpportunityAdvisor
from product_intelligence.services.comparable_price_summary import ComparablePriceSummaryService
from product_intelligence.services.opportunity_commercial_recalculation import OpportunityCommercialRecalculationService
from product_intelligence.services.pricing_policy import get_market_price_reference
from product_intelligence.services.opportunity_recommendation_service import OpportunityRecommendationService


class OpportunityAIRecommendationRunner:
    @classmethod
    def run(cls, opportunity, engine, model_name="", review_context=None):
        comparables = ComparablePriceSummaryService.summarize(opportunity.supplier_offer, "EUR") if opportunity.supplier_offer_id else None
        median_price = comparables["median_price"] if comparables else None
        commercial_median_price = comparables["commercial_median_price"] if comparables else None
        pricing = OpportunityCommercialRecalculationService.calculate(opportunity, market_summary=comparables) if comparables else {"status": "incomplete"}
        if pricing["status"] == "ready" and opportunity.status in ("detected", "review"):
            fields = ("recommended_price", "other_costs", "projected_profit", "projected_margin_rate", "opportunity_score")
            for field in fields:
                setattr(opportunity, field, pricing[field])
            opportunity.save(update_fields=[*fields, "updated_at"])
        analysis = OpportunityAdvisor.get_recommendation(opportunity)
        price_gap_percent = round((opportunity.recommended_price / commercial_median_price - 1) * 100, 2) if commercial_median_price and opportunity.recommended_price is not None else None
        complete = (analysis["analysis_complete"] and opportunity.saturation_level != "indeterminate")
        reference_type = get_market_price_reference()
        reference_field = {"minimum": "minimum_price", "median": "commercial_median_price", "maximum": "maximum_price"}[reference_type]
        financial_context = {"break_even_price": pricing.get("break_even_price"), "minimum_profitable_price": pricing.get("minimum_profitable_price"), "pricing_policy": pricing.get("pricing_policy"), "market_reference_type": reference_type, "market_reference_price": comparables.get(reference_field) if comparables else None, "projected_profit": opportunity.projected_profit, "projected_margin_rate": opportunity.projected_margin_rate, "pricing_status": pricing["status"]}
        service = OpportunityRecommendationService(engine=engine)
        from products.models import Category
        categories = list(Category.objects.select_related("parent", "parent__parent").order_by("id"))
        existing_category_paths = [[c.parent.parent.name, c.parent.name, c.name] if c.parent and c.parent.parent else ([c.parent.name, c.name] if c.parent else [c.name]) for c in categories]
        initial_category_path = opportunity.supplier_offer.product_idea.category_path if opportunity.supplier_offer_id and opportunity.supplier_offer.product_idea_id else []
        result = service.recommend(additional_instructions=review_context, product_data={"initial_category_path": initial_category_path, "existing_category_paths": existing_category_paths, "commercial_product_context": {"idea_name": opportunity.supplier_offer.product_idea.name if opportunity.supplier_offer_id and opportunity.supplier_offer.product_idea_id else "", "customer_problem": opportunity.supplier_offer.product_idea.customer_problem if opportunity.supplier_offer_id and opportunity.supplier_offer.product_idea_id else "", "target_customer": opportunity.supplier_offer.product_idea.target_customer if opportunity.supplier_offer_id and opportunity.supplier_offer.product_idea_id else "", "supplier_product_name": opportunity.supplier_offer.product_name if opportunity.supplier_offer_id else "", "supplier_product_description": opportunity.supplier_offer.product_description if opportunity.supplier_offer_id else ""}, "name": opportunity.name, "supplier_price": opportunity.supplier_price, "market_price": opportunity.market_price, "shipping_cost": opportunity.shipping_cost, "recommended_price": opportunity.recommended_price, "financial_context": financial_context, "saturation_level": opportunity.saturation_level, "market_comparables": {"minimum_price": comparables["minimum_price"], "median_price": median_price, "commercial_median_price": comparables["commercial_median_price"], "maximum_price": comparables["maximum_price"], "retained_count": comparables["retained_count"], "source_domain_count": comparables["source_domain_count"], "price_gap_percent": price_gap_percent, "competitor_shipping_included": "unknown", "shipping_comparables": comparables["shipping_comparables"]} if comparables else None, "supplier_logistics": {"shipping_days": opportunity.supplier_offer.shipping_days, "shipping_country": opportunity.supplier_offer.shipping_country, "shipping_method": opportunity.supplier_offer.shipping_method, "customs_included": opportunity.supplier_offer.customs_included, "free_shipping": opportunity.supplier_offer.free_shipping} if opportunity.supplier_offer_id else None}, score_data={"score": opportunity.opportunity_score, "reasons": analysis["reasons"], "analysis_complete": complete, "missing_competition": opportunity.saturation_level == "indeterminate", "missing_demand": opportunity.demand_score <= 0})
        from products.services.category_validation import CategoryValidationService
        proposed_category_path = result.get("category_path", [])
        validated_category_path = proposed_category_path if CategoryValidationService.validate(proposed_category_path) else []
        recommendation, created = OpportunityAIRecommendation.objects.update_or_create(opportunity=opportunity, defaults={"decision": result["decision"], "summary": result["summary"], "merchant_summary": result.get("merchant_summary", ""), "commercial_name": result.get("commercial_name") or getattr(getattr(opportunity, "ai_recommendation", None), "commercial_name", ""), "commercial_description": result.get("commercial_description") or getattr(getattr(opportunity, "ai_recommendation", None), "commercial_description", ""), "category_path": validated_category_path, "category_reason": result.get("category_reason", ""), "study_blockers": result.get("study_blockers", []) if result["decision"] == "study" else [], "model_name": model_name if complete else ""})
        commercial_updates = []
        commercial_name = (recommendation.commercial_name or "").strip()
        commercial_description = (recommendation.commercial_description or "").strip()
        if commercial_name and (not opportunity.name or opportunity.name == getattr(getattr(opportunity, "supplier_offer", None), "product_name", None)):
            opportunity.name = commercial_name
            commercial_updates.append("name")
        if not commercial_description and not (opportunity.description or "").strip():
            from dashboard.services.description_suggestion_service import DescriptionSuggestionService
            commercial_description = (DescriptionSuggestionService.suggest(opportunity) or "").strip()
        if commercial_description and opportunity.status in ('detected', 'review'):
            opportunity.description = commercial_description
            commercial_updates.append("description")
        if commercial_updates:
            opportunity.save(update_fields=commercial_updates)
        if validated_category_path and result.get("category_reason", "").strip():
            from products.services.category_normalization import CategoryNormalizationService
            from products.services.opportunity_category_assignment import OpportunityCategoryAssignmentService
            matches = CategoryNormalizationService.propose(validated_category_path)
            if len(matches) == 3:
                OpportunityCategoryAssignmentService.assign(opportunity, validated_category_path, result["category_reason"])
        return recommendation

    @classmethod
    def run_with_openai(cls, opportunity, model=None, review_context=None):
        import os
        import ssl
        import httpx
        import truststore
        from openai import OpenAI
        from product_intelligence.services.ai_recommendation_engine import AIRecommendationEngine
        from product_intelligence.services.openai_client import OpenAIClient

        selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        if opportunity.saturation_level == "indeterminate" or opportunity.opportunity_score is None:
            return cls.run(opportunity, engine=None, review_context=review_context)

        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context, timeout=180.0) as http_client:
            sdk_client = OpenAI(http_client=http_client)
            ai_client = OpenAIClient(client=sdk_client, model=selected_model)
            engine = AIRecommendationEngine(client=ai_client)
            return cls.run(opportunity, engine=engine, model_name=selected_model, review_context=review_context)
