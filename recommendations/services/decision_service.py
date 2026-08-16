"""
RecommendationDecisionService

Responsabilité
--------------
Orchestrer l'exécution des décisions prises par le commerçant
dans le Centre de recommandations.

Ce service :
- publie une recommandation ;
- délègue l'exécution aux services métier appropriés.

Fonctionnalités prévues :
- reporter une recommandation ;
- rejeter une recommandation.

Ce service ne :
- ne contient pas la logique métier de publication ;
- ne crée pas directement de produit ;
- ne choisit pas la décision à la place du commerçant.

Utilisé par
-----------
- recommendations.views

Dépend de
---------
- ProductOpportunity
- OpportunityPublisher
"""

from product_intelligence.models import ProductOpportunity
from product_intelligence.services.publisher import OpportunityPublisher

from datetime import timedelta
from django.utils import timezone


class RecommendationDecisionService:
    @staticmethod
    def publish(opportunity: ProductOpportunity):
        return OpportunityPublisher.publish(opportunity)

    @staticmethod
    def postpone(opportunity: ProductOpportunity):
        if opportunity.status != "approved":
            raise ValueError(
                "Cette opportunité doit être approuvée."
            )

        if opportunity.published_product:
            raise ValueError(
                "Cette opportunité est déjà publiée."
            )

        opportunity.postponed_until = (
            timezone.now() + timedelta(days=14)
        )

        opportunity.save(
            update_fields=[
                "postponed_until",
                "updated_at",
            ]
        )

        return opportunity

    @staticmethod
    def reject(opportunity: ProductOpportunity):
        if opportunity.published_product:
            raise ValueError(
                "Une opportunité déjà publiée ne peut pas être rejetée."
            )

        if opportunity.status != "approved":
            raise ValueError(
                "Cette opportunité doit être approuvée."
            )

        opportunity.status = "rejected"

        opportunity.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return opportunity
        
        