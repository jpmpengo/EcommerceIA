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

        opportunity.save()

        if self.decision_service is not None:
            opportunity = (
                self.decision_service.evaluate(
                    opportunity
                )
            )

        return opportunity
