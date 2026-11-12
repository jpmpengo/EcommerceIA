from decimal import Decimal

from product_intelligence.models import ProductOpportunity

from product_intelligence.services.restock_opportunity import (
    RestockOpportunityService,
)

from product_intelligence.services.supplier_product_matching import (
    SupplierProductMatchingService,
)

class SupplierOfferOpportunityService:

    def __init__(
        self,
        minimum_margin=None,
        minimum_score=None,
        minimum_stock=None,
        decision_service=None,
    ):
        self.minimum_margin = minimum_margin
        self.minimum_score = minimum_score
        self.minimum_stock = minimum_stock
        self.decision_service = decision_service

    @staticmethod
    def resolve_category(offer):
        from products.models import Category
        from products.services.category_normalization import CategoryNormalizationService

        idea = offer.product_idea
        if idea is None or not idea.category_path:
            return None

        matches = CategoryNormalizationService.propose(idea.category_path)
        if not matches or len(matches) < 2 or any(item['needs_approval'] for item in matches[:2]) or any(item['needs_approval'] for item in matches[2:-1]):
            return None

        return Category.objects.get(pk=next(item['category_id'] for item in reversed(matches) if item['category_id'] is not None))

    def total_cost(
        self,
        offer,
    ):
        if offer.shipping_cost is None:
            return None

        return (
            offer.purchase_price
            + offer.shipping_cost
        )

    def estimated_margin(
        self,
        offer,
        market_price,
    ):
        total_cost = self.total_cost(
            offer
        )

        if total_cost is None:
            return None

        return (
            market_price
            - total_cost
        )

    def margin_percent(
        self,
        offer,
        market_price,
    ):
        total_cost = self.total_cost(
            offer
        )

        if (
            total_cost is None
            or total_cost == 0
        ):
            return Decimal("0.00")

        margin = self.estimated_margin(
            offer,
            market_price,
        )

        return (
            margin
            / total_cost
            * Decimal("100")
        ).quantize(
            Decimal("0.01")
        )

    def create_opportunity(
        self,
        offer,
        market_price,
    ):
        if offer.shipping_cost is None:
            return None

        if (
            self.minimum_stock is not None
            and (
                offer.stock is None
                or offer.stock < self.minimum_stock
            )
        ):
            return None

        margin = self.estimated_margin(
            offer,
            market_price,
        )

        if (
            self.minimum_margin is not None
            and margin < self.minimum_margin
        ):
            return None

        restock_product = (
            RestockOpportunityService.find_product(
                offer
            )
        )

        opportunity = ProductOpportunity(
            name=offer.product_name,
            source_name=offer.supplier.name,
            source_url=offer.product_url,
            supplier_price=offer.purchase_price,
            market_price=market_price,
            shipping_cost=offer.shipping_cost,
            supplier_offer=offer,
            category=self.resolve_category(offer),
            restock_product=restock_product,
        )

        score = (
            opportunity
            .calculate_opportunity_score()
        )

        if (
            self.minimum_score is not None
            and score < self.minimum_score
        ):
            return None

        opportunity.opportunity_score = score
        opportunity.save()

        if self.decision_service is not None:
            opportunity = (
                self.decision_service.evaluate(
                    opportunity
                )
            )

        return opportunity

    def create_analyzed_opportunity(
        self,
        offer,
        decision_price,
        base_cost_result,
        cost_result,
        market_collection_batch_id=None,
        market_summary=None,
    ):
        """Persist an opportunity whose costs share the market currency."""
        if (
            self.minimum_stock is not None
            and (
                offer.stock is None
                or offer.stock < self.minimum_stock
            )
        ):
            return None

        if (
            self.minimum_margin is not None
            and cost_result["projected_profit"]
            < self.minimum_margin
        ):
            return None

        additional_costs = (
            cost_result["vat_amount"]
            + cost_result["import_duty"]
            + cost_result["payment_fee"]
            + cost_result["return_reserve"]
            + cost_result["safety_reserve"]
        )

        restock_product = (
            RestockOpportunityService.find_product(
                offer
            )
        )

        from product_intelligence.services.demand_score_service import DemandScoreService

        product_idea = offer.product_idea
        demand_score = DemandScoreService.calculate(
            product_idea.demand_signal_assessments
            if product_idea is not None
            else []
        )

        from product_intelligence.services.competition_score_service import CompetitionScoreService
        competition_score = CompetitionScoreService.calculate(market_summary or {})

        opportunity = ProductOpportunity(
            name=offer.product_name,
            source_name=offer.supplier.name,
            source_url=offer.product_url,
            supplier_price=(
                base_cost_result["purchase_converted"]
            ),
            shipping_cost=(
                base_cost_result["shipping_converted"]
            ),
            shipping_cost_is_known=True,
            other_costs=additional_costs,
            market_price=decision_price,
            recommended_price=decision_price,
            projected_profit=cost_result["projected_profit"],
            projected_margin_rate=cost_result["projected_margin_rate"],
            market_collection_batch_id=market_collection_batch_id,
            supplier_offer=offer,
            category=self.resolve_category(offer),
            restock_product=restock_product,
            demand_score=demand_score,
            competition_score=competition_score,
        )

        opportunity.save()

        if self.decision_service is not None:
            opportunity = (
                self.decision_service.evaluate(
                    opportunity
                )
            )

        return opportunity
