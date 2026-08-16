"""
OpportunityAnalyzer

Responsabilité
--------------
Calculer les indicateurs métier d'une opportunité.

Ce service :
- calcule les coûts ;
- calcule les marges ;
- calcule le score d'opportunité ;
- calcule le prix recommandé.

Ce service ne modifie jamais la base de données.

"""

"""
OpportunityAnalyzer

Responsabilité :
Calculer les indicateurs métier d'une opportunité.

Ne modifie jamais la base de données.

Utilisé par :
- ProductOpportunity
- OpportunityAdvisor
"""

class OpportunityAnalyzer:

    @staticmethod
    def total_cost(opportunity):
        return (
            opportunity.supplier_price
            + opportunity.shipping_cost
            + opportunity.other_costs
        )

    @staticmethod
    def estimated_margin(opportunity):
        return (
            opportunity.market_price
            - OpportunityAnalyzer.total_cost(opportunity)
        )

    @staticmethod
    def margin_percent(opportunity):
        total_cost = OpportunityAnalyzer.total_cost(opportunity)

        if total_cost == 0:
            return 0

        return (
            OpportunityAnalyzer.estimated_margin(opportunity)
            / total_cost
        ) * 100

    @staticmethod
    def opportunity_score(opportunity):
        score = 0

        if OpportunityAnalyzer.margin_percent(opportunity) >= 50:
            score += 40

        if opportunity.demand_score >= 80:
            score += 30

        if opportunity.competition_score <= 50:
            score += 20

        return min(score, 100)

    @staticmethod
    def recommended_price(opportunity):
        if opportunity.recommended_price is not None:
            return opportunity.recommended_price

        return opportunity.market_price


