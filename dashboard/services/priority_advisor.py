from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from product_intelligence.models import ProductOpportunity
from product_intelligence.services.advisor import OpportunityAdvisor

from dashboard.services.publication_readiness_service import (
    PublicationReadinessService,
)


class PriorityAdvisor:

    @staticmethod
    def get_priority():
        opportunities = (
            ProductOpportunity.objects
            .filter(
                status="approved",
                published_product__isnull=True,
                restock_product__isnull=True,
                category__isnull=False,
            )
            .filter(
                Q(postponed_until__isnull=True)
                | Q(postponed_until__lte=timezone.now())
            )
        )

        opportunity = None

        for candidate in opportunities:
            readiness = PublicationReadinessService.evaluate(
                candidate
            )

            if readiness["ready"]:
                opportunity = candidate
                break

        if opportunity is None:
            return None

        recommendation = OpportunityAdvisor.get_recommendation(
            opportunity
        )

        return {
            "opportunity": opportunity,
            "title": f"Publier {opportunity.name}",
            "message": (
                "Je pense que cette publication est "
                "votre meilleure opportunité aujourd’hui."
            ),
            "reasons": recommendation["reasons"],
            "action_label": "Voir la recommandation",
            "action_url": reverse(
                "recommendations:detail",
                args=[opportunity.pk],
            ),
        }

        

        

