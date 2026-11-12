from product_intelligence.services.opportunity_profitability_score import OpportunityProfitabilityScoreService
from product_intelligence.services.opportunity_demand_score import OpportunityDemandScoreService
from product_intelligence.services.opportunity_saturation_score import OpportunitySaturationScoreService


class OpportunityCommercialScoreService:
    @staticmethod
    def calculate(margin_rate, demand_score, saturation_level):
        saturation_points = OpportunitySaturationScoreService.calculate(saturation_level)
        if saturation_points is None:
            return None
        profitability_points = OpportunityProfitabilityScoreService.calculate(margin_rate)
        demand_points = OpportunityDemandScoreService.calculate(demand_score)
        return profitability_points + demand_points + saturation_points
