from collections import defaultdict

from product_intelligence.models import (
    ProductOpportunity,
)
from product_intelligence.services.comparable_price_runner_factory import (
    ComparablePriceRunnerFactory,
)
from product_intelligence.services.supplier_candidate_collection_runner import (
    SupplierCandidateCollectionRunner,
)
from product_intelligence.services.supplier_offer_analysis_runner import (
    SupplierOfferAnalysisRunner,
)


class ProductIdeaManualAnalysisService:
    """Exécute manuellement le même parcours destiné au futur travail nocturne."""

    @staticmethod
    def build_saturation_service():
        from product_intelligence.services.product_idea_generation import ProductIdeaGenerationService
        from product_intelligence.services.opportunity_saturation_search import OpportunitySaturationSearchService
        discovery = ProductIdeaGenerationService._build_discovery_service(model=ProductIdeaGenerationService.DEFAULT_MODEL)
        return OpportunitySaturationSearchService(client=discovery.client)

    PRIORITY_MAXIMUM_DAYS = 20
    FALLBACK_MAXIMUM_DAYS = 50

    @classmethod
    def run(
        cls,
        product_idea,
        candidate_collector=None,
        comparable_runner=None,
        analysis_runner=None,
        economic_fallback=None,
    ):
        if product_idea.status not in {"selected", "validated"}:
            raise ValueError(
                "Seule une idée sélectionnée peut être étudiée."
            )

        collector = (
            candidate_collector
            or SupplierCandidateCollectionRunner
        )
        prices = (
            comparable_runner
            or ComparablePriceRunnerFactory.build()
        )
        analyzer = (
            analysis_runner
            or SupplierOfferAnalysisRunner()
        )
        fallback = economic_fallback

        supplier_summary = collector.collect(
            product_idea=product_idea
        )
        comparison_summary = prices.run(
            product_idea=product_idea
        )

        viable_by_supplier = defaultdict(list)
        analyzed_count = 0
        unprofitable_count = 0
        customs_excluded_count = 0
        incomplete_count = 0
        has_viable_cj_offer = False

        offers = (
            product_idea.supplier_offers
            .select_related("supplier")
            .all()
        )
        if product_idea.visual_references.exists():
            offers = offers.exclude(
                visual_match_classification=""
            ).exclude(
                visual_match_classification="rejected"
            )

        for offer in offers:
            analyzed_count += 1
            from product_intelligence.services.supplier_offer_initial_study_completion import SupplierOfferInitialStudyCompletionService
            result = SupplierOfferInitialStudyCompletionService.analyze(analyzer, offer)
            status = result.get("status")

            if status == "ready_for_opportunity":
                shipping_days = offer.shipping_days
                if (
                    shipping_days is not None
                    and shipping_days
                    <= cls.FALLBACK_MAXIMUM_DAYS
                ):
                    viable_by_supplier[
                        offer.supplier_id
                    ].append((offer, result))
                    if (
                        offer.supplier.name
                        == "CJdropshipping"
                    ):
                        has_viable_cj_offer = True
            elif status == "customs_excluded":
                customs_excluded_count += 1
                ProductOpportunity.objects.filter(supplier_offer=offer, status="review").update(status="rejected")
                ProductOpportunity.objects.filter(supplier_offer=offer, status="approved").update(status="review", market_collection_batch_id=None)
            elif status == "unprofitable":
                unprofitable_count += 1
                ProductOpportunity.objects.filter(
                    supplier_offer=offer,
                    status="review",
                ).update(status="rejected")
                ProductOpportunity.objects.filter(
                    supplier_offer=offer,
                    status="approved",
                ).update(
                    status="review",
                    market_collection_batch_id=None,
                )
            else:
                incomplete_count += 1
                ProductOpportunity.objects.filter(
                    supplier_offer=offer,
                    status="review",
                ).update(status="rejected")
                ProductOpportunity.objects.filter(
                    supplier_offer=offer,
                    status="approved",
                ).update(
                    status="review",
                    market_collection_batch_id=None,
                )

        has_cn_offer = product_idea.supplier_offers.filter(
            supplier__name="CJdropshipping",
            stock_country="CN",
        ).exists()

        if (
            not has_viable_cj_offer
            and not has_cn_offer
        ):
            if fallback is None:
                fallback = (
                    ComparablePriceRunnerFactory
                    .build_economic_fallback()
                )

            if fallback is not None:
                fallback_offers = fallback.run(
                    product_idea=product_idea,
                )
            else:
                fallback_offers = []

            for offer in fallback_offers:
                analyzed_count += 1
                result = SupplierOfferInitialStudyCompletionService.analyze(analyzer, offer)
                status = result.get("status")

                if status == "ready_for_opportunity":
                    shipping_days = offer.shipping_days
                    if (
                        shipping_days is not None
                        and shipping_days
                        <= cls.FALLBACK_MAXIMUM_DAYS
                    ):
                        viable_by_supplier[
                            offer.supplier_id
                        ].append((offer, result))
                elif status == "customs_excluded":
                    customs_excluded_count += 1
                elif status == "unprofitable":
                    unprofitable_count += 1
                else:
                    incomplete_count += 1

        selected = []
        for candidates in viable_by_supplier.values():
            priority_candidates = [
                item
                for item in candidates
                if item[0].shipping_days
                <= cls.PRIORITY_MAXIMUM_DAYS
            ]
            retained_pool = (
                priority_candidates
                or candidates
            )
            retained = min(
                retained_pool,
                key=cls._selection_key,
            )
            selected.append(retained)

        saturation_result = None
        if selected:
            saturation_result = cls.build_saturation_service().search(
                product_name=product_idea.name,
                product_attributes={"customer_problem": product_idea.customer_problem, "target_customer": product_idea.target_customer, "countries": product_idea.countries},
            )

        from product_intelligence.services.opportunity_commercial_score import OpportunityCommercialScoreService
        def apply_commercial_analysis(opportunity):
            if saturation_result is None:
                return opportunity
            if saturation_result.get("all_urls_invalid"):
                opportunity.status = "rejected"
                opportunity.saturation_level = "indeterminate"
                opportunity.opportunity_score = None
                opportunity.saturation_evidence = {**saturation_result, "validation_reason": "Aucune preuve concurrentielle exploitable"}
                opportunity.save(update_fields=["status", "saturation_level", "opportunity_score", "saturation_evidence", "updated_at"])
                return opportunity
            opportunity.saturation_level = saturation_result["level"]
            opportunity.saturation_evidence = saturation_result
            total_cost = opportunity.supplier_price + opportunity.shipping_cost + opportunity.other_costs
            margin_rate = ((opportunity.market_price - total_cost) / total_cost * 100) if total_cost > 0 else 0
            opportunity.opportunity_score = OpportunityCommercialScoreService.calculate(margin_rate, opportunity.demand_score, opportunity.saturation_level)
            opportunity.save(update_fields=["saturation_level", "saturation_evidence", "opportunity_score", "updated_at"])
            return opportunity

        created = []
        processed_opportunity_ids = []
        already_existing = 0
        for offer, unused_result in selected:
            existing_opportunity = (
                ProductOpportunity.objects.filter(
                    supplier_offer=offer,
                ).first()
            )
            if existing_opportunity is not None:
                already_existing += 1
                if existing_opportunity.status == "review":
                    decision_price = unused_result["dossier"]["decision_price"]
                    base_cost = unused_result["base_cost"]
                    cost_analysis = unused_result["cost_analysis"]
                    additional_costs = (
                        cost_analysis["vat_amount"]
                        + cost_analysis["import_duty"]
                        + cost_analysis["payment_fee"]
                        + cost_analysis["return_reserve"]
                        + cost_analysis["safety_reserve"]
                    )
                    existing_opportunity.supplier_price = base_cost["purchase_converted"]
                    existing_opportunity.shipping_cost = base_cost["shipping_converted"]
                    existing_opportunity.shipping_cost_is_known = True
                    existing_opportunity.other_costs = additional_costs
                    existing_opportunity.market_price = decision_price
                    existing_opportunity.recommended_price = decision_price
                    existing_opportunity.market_collection_batch_id = (
                        unused_result.get("dossier", {})
                        .get("market", {})
                        .get("collection_batch_id")
                    )
                    from product_intelligence.services.demand_score_service import DemandScoreService
                    existing_opportunity.demand_score = DemandScoreService.calculate(
                        offer.product_idea.demand_signal_assessments
                        if offer.product_idea is not None
                        else []
                    )
                    from product_intelligence.services.competition_score_service import CompetitionScoreService
                    existing_opportunity.competition_score = CompetitionScoreService.calculate(
                        unused_result.get("dossier", {}).get("market", {})
                    )
                    existing_opportunity.opportunity_score = None
                    existing_opportunity.save(
                        update_fields=[
                            "supplier_price",
                            "shipping_cost",
                            "shipping_cost_is_known",
                            "other_costs",
                            "market_price",
                            "recommended_price",
                            "market_collection_batch_id",
                            "demand_score",
                            "competition_score",
                            "opportunity_score",
                            "updated_at",
                        ]
                    )
                if existing_opportunity.status == "review":
                    apply_commercial_analysis(existing_opportunity)
                    if existing_opportunity.status == "review":
                        processed_opportunity_ids.append(existing_opportunity.pk)
                continue

            result = analyzer.process(
                supplier_offer=offer,
                create=True,
            )
            opportunity = result.get("opportunity")
            if opportunity is not None:
                opportunity.status = "review"
                opportunity.save(
                    update_fields=[
                        "status",
                        "opportunity_score",
                        "updated_at",
                    ]
                )
                apply_commercial_analysis(opportunity)
                created.append(opportunity)
                if opportunity.status == "review":
                    processed_opportunity_ids.append(opportunity.pk)

        if analyzed_count > 0 and customs_excluded_count == analyzed_count:
            product_idea.status = "rejected"
            product_idea.save(update_fields=["status", "updated_at"])
            return {"product_idea_id": product_idea.pk, "status": "rejected", "reason": "all_offers_customs_excluded", "offers_analyzed": analyzed_count, "offers_customs_excluded": customs_excluded_count, "offers_retained": 0, "opportunities_created": 0, "processed_opportunity_ids": []}

        product_idea.status = "validated"
        product_idea.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return {
            "product_idea_id": product_idea.pk,
            "supplier_summary": supplier_summary,
            "comparison_summary": comparison_summary,
            "offers_analyzed": analyzed_count,
            "offers_unprofitable": unprofitable_count,
            "offers_customs_excluded": customs_excluded_count,
            "offers_incomplete": incomplete_count,
            "offers_retained": len(selected),
            "opportunities_created": len(created),
            "opportunities_existing": already_existing,
            "processed_opportunity_ids": processed_opportunity_ids,
            "opportunity_ids": [
                opportunity.pk
                for opportunity in created
            ],
        }

    @classmethod
    def refresh_existing_review_opportunity(
        cls,
        opportunity,
        offer,
        analysis_result,
    ):
        if opportunity.status != "review":
            return opportunity

        decision_price = analysis_result["dossier"]["decision_price"]
        base_cost = analysis_result["base_cost"]
        cost_analysis = analysis_result["cost_analysis"]
        additional_costs = (
            cost_analysis["vat_amount"]
            + cost_analysis["import_duty"]
            + cost_analysis["payment_fee"]
            + cost_analysis["return_reserve"]
            + cost_analysis["safety_reserve"]
        )

        opportunity.supplier_price = base_cost["purchase_converted"]
        opportunity.shipping_cost = base_cost["shipping_converted"]
        opportunity.shipping_cost_is_known = True
        opportunity.other_costs = additional_costs
        opportunity.market_price = decision_price
        opportunity.recommended_price = decision_price
        opportunity.market_collection_batch_id = (
            analysis_result.get("dossier", {})
            .get("market", {})
            .get("collection_batch_id")
        )

        from product_intelligence.services.demand_score_service import DemandScoreService
        opportunity.demand_score = DemandScoreService.calculate(
            offer.product_idea.demand_signal_assessments
            if offer.product_idea is not None
            else []
        )

        from product_intelligence.services.competition_score_service import CompetitionScoreService
        opportunity.competition_score = CompetitionScoreService.calculate(
            analysis_result.get("dossier", {}).get("market", {})
        )

        opportunity.opportunity_score = None

        opportunity.save(
            update_fields=[
                "supplier_price",
                "shipping_cost",
                "shipping_cost_is_known",
                "other_costs",
                "market_price",
                "recommended_price",
                "market_collection_batch_id",
                "demand_score",
                "competition_score",
                "opportunity_score",
                "updated_at",
            ]
        )

        return opportunity

    @classmethod
    def _selection_key(cls, item):
        offer, result = item
        base_cost = result["base_cost"]["base_cost"]
        profit = result["cost_analysis"][
            "projected_profit"
        ]
        return (
            base_cost,
            -profit,
            offer.shipping_days,
            offer.pk,
        )
