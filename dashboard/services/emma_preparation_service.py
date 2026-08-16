from product_intelligence.models import (
    ProductOpportunity,
)

from dashboard.services.publication_readiness_service import (
    PublicationReadinessService,
)


class EmmaPreparationService:

    @staticmethod
    def get_items():
        items = []

        opportunities = (
            ProductOpportunity.objects.filter(
                status="approved",
                published_product__isnull=True,
                restock_product__isnull=True,
            )
        )

        for opportunity in opportunities:
            readiness = (
                PublicationReadinessService.evaluate(
                    opportunity
                )
            )

            if readiness["ready"]:
                continue

            items.append(
                {
                    "opportunity": opportunity,
                    "title": opportunity.name,
                    "missing": readiness["missing"],
                }
            )

        return items

        
