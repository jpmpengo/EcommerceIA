"""
OpportunityAdvisor

Responsabilité
--------------
Transformer les analyses d'une opportunité en une recommandation
compréhensible par le commerçant.

Ce service :
- interprète les indicateurs calculés par OpportunityAnalyzer ;
- formule une recommandation ;
- explique les raisons de cette recommandation ;
- estime le niveau de confiance.

Ce service ne :
- modifie jamais la base de données ;
- crée jamais de produit ;
- prend jamais de décision à la place du commerçant.
"""

from .analyzer import OpportunityAnalyzer


class OpportunityAdvisor:

    @staticmethod
    def get_recommendation(opportunity):
        reasons = []

        margin_percent = (
            OpportunityAnalyzer.margin_percent(
                opportunity
            )
        )

        estimated_margin = (
            OpportunityAnalyzer.estimated_margin(
                opportunity
            )
        )

        score = (
            OpportunityAnalyzer.opportunity_score(
                opportunity
            )
        )

        if margin_percent >= 50:
            reasons.append(
                (
                    "Marge élevée : "
                    f"{margin_percent:.1f} %."
                )
            )

        elif margin_percent >= 30:
            reasons.append(
                (
                    "Marge intéressante : "
                    f"{margin_percent:.1f} %."
                )
            )

        else:
            reasons.append(
                (
                    "Marge limitée : "
                    f"{margin_percent:.1f} %."
                )
            )

        if opportunity.demand_score <= 0:
            reasons.append(
                "Demande non renseignée."
            )

        elif opportunity.demand_score >= 80:
            reasons.append(
                "Demande forte."
            )

        elif opportunity.demand_score >= 60:
            reasons.append(
                "Demande correcte."
            )

        else:
            reasons.append(
                "Demande faible."
            )

        if opportunity.competition_score <= 0:
            reasons.append(
                "Concurrence non renseignée."
            )

        elif opportunity.competition_score <= 30:
            reasons.append(
                "Concurrence faible."
            )

        elif opportunity.competition_score <= 60:
            reasons.append(
                "Concurrence modérée."
            )

        else:
            reasons.append(
                "Concurrence élevée."
            )

        if score >= 80:
            decision = (
                "Je recommande d'examiner ce produit."
            )

            level = "success"

        elif score >= 60:
            decision = (
                "Cette opportunité mérite une "
                "préparation avant décision de "
                "publication."
            )

            level = "warning"

        else:
            decision = (
                "Je ne recommande pas ce produit "
                "actuellement."
            )

            level = "danger"

        return {
            "score": score,
            "estimated_margin": estimated_margin,
            "margin_percent": margin_percent,
            "reasons": reasons,
            "decision": decision,
            "level": level,
        }

    @staticmethod
    def calculate_priority(opportunity):
        """
        Calcule la priorité actuelle d'une opportunité.

        Pour l'instant, la priorité correspond au score
        calculé par OpportunityAnalyzer.
        """

        return (
            OpportunityAnalyzer.opportunity_score(
                opportunity
            )
        )

    @staticmethod
    def rank_opportunities(opportunities):
        return sorted(
            opportunities,
            key=(
                OpportunityAdvisor
                .calculate_priority
            ),
            reverse=True,
        )
