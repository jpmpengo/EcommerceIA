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

        score = opportunity.opportunity_score

        margin_is_reliable = (
            OpportunityAnalyzer
            .margin_is_reliable(
                opportunity
            )
        )

        if not margin_is_reliable:
            reasons.append(
                (
                    "Marge provisoire : les frais "
                    "de livraison ne sont pas "
                    "vérifiés."
                )
            )

        elif margin_percent >= 50:
            reasons.append(
                (
                    "Rendement sur coût élevé : "
                    f"{margin_percent:.1f} %."
                )
            )

        elif margin_percent >= 30:
            reasons.append(
                (
                    "Rendement sur coût intéressant : "
                    f"{margin_percent:.1f} %."
                )
            )

        else:
            reasons.append(
                (
                    "Rendement sur coût limité : "
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

        if opportunity.saturation_level in ("high", "very_high"):
            reasons.append("Concurrence forte.")
        elif opportunity.saturation_level == "moderate":
            reasons.append("Concurrence moyenne.")
        elif opportunity.saturation_level in ("low", "very_low"):
            reasons.append("Concurrence faible.")
        else:
            reasons.append("Concurrence non evaluee.")

        market_scores_are_missing = (
            opportunity.demand_score <= 0
            or opportunity.competition_score <= 0
        )

        if market_scores_are_missing or score is None:
            decision = (
                "Les données de demande et de concurrence "
                "doivent être complétées avant recommandation."
            )
            level = "warning"

        elif score >= 80:
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
            "analysis_complete": (
                not market_scores_are_missing and score is not None
            ),
            "estimated_margin": estimated_margin,
            "margin_percent": margin_percent,
            "margin_is_reliable": (
                margin_is_reliable
            ),
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

        return opportunity.opportunity_score

    @staticmethod
    def rank_opportunities(opportunities):
        return sorted(
            opportunities,
            key=lambda opportunity: (
                OpportunityAdvisor.calculate_priority(opportunity) is not None,
                OpportunityAdvisor.calculate_priority(opportunity) if OpportunityAdvisor.calculate_priority(opportunity) is not None else -1,
            ),
            reverse=True,
        )
