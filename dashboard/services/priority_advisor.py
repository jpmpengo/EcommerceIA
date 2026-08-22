from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from dashboard.services.publication_readiness_service import (
    PublicationReadinessService,
)
from product_intelligence.models import (
    ProductOpportunity,
)
from product_intelligence.services.advisor import (
    OpportunityAdvisor,
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
            )
            .filter(
                Q(
                    postponed_until__isnull=True
                )
                | Q(
                    postponed_until__lte=(
                        timezone.now()
                    )
                )
            )
        )

        ready_opportunity = None
        preparation_opportunity = None

        for candidate in opportunities:
            readiness = (
                PublicationReadinessService
                .evaluate(
                    candidate
                )
            )

            if readiness["ready"]:
                ready_opportunity = candidate
                break

            if preparation_opportunity is None:
                preparation_opportunity = (
                    candidate
                )

        if ready_opportunity is not None:
            opportunity = ready_opportunity
            action_mode = "publish"

        elif preparation_opportunity is not None:
            opportunity = preparation_opportunity
            action_mode = "prepare"

        else:
            return None

        recommendation = (
            OpportunityAdvisor
            .get_recommendation(
                opportunity
            )
        )

        if action_mode == "publish":
            title = (
                f"Publier {opportunity.name}"
            )

            message = (
                "Ce produit est prêt. "
                "Je vous conseille de vérifier "
                "une dernière fois la recommandation "
                "avant sa publication."
            )

            action_label = (
                "Voir la recommandation"
            )

        else:
            title = (
                f"Préparer {opportunity.name}"
            )

            message = (
                "Ce produit a été approuvé, "
                "mais certaines informations doivent "
                "encore être complétées avant sa "
                "publication."
            )

            action_label = (
                "Préparer ce produit"
            )

        return {
            "opportunity": opportunity,
            "title": title,
            "message": message,
            "reasons": recommendation[
                "reasons"
            ],
            "action_label": action_label,
            "action_url": reverse(
                "recommendations:detail",
                args=[
                    opportunity.pk,
                ],
            ),
        }
        

        

