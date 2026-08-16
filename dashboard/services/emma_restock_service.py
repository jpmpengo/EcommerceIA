from product_intelligence.models import (
    ProductOpportunity,
)

from dashboard.services.stock_suggestion_service import (
    StockSuggestionService,
)


class EmmaRestockService:

    @staticmethod
    def get_items():
        items = []

        opportunities = (
            ProductOpportunity.objects
            .filter(
                status="approved",
                restock_product__isnull=False,
            )
            .select_related(
                "restock_product",
                "supplier_offer",
            )
        )

        for opportunity in opportunities:
            suggested_stock = (
                StockSuggestionService.suggest(
                    opportunity
                )
            )

            supplier_stock = None

            if opportunity.supplier_offer is not None:
                supplier_stock = (
                    opportunity.supplier_offer.stock
                )

            items.append(
                {
                    "opportunity": opportunity,
                    "product": opportunity.restock_product,
                    "title": opportunity.name,
                    "current_stock": (
                        opportunity.restock_product.stock
                    ),
                    "supplier_stock": supplier_stock,
                    "suggested_stock": suggested_stock,
                }
            )

        return items

        