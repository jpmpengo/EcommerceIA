from decimal import Decimal, ROUND_HALF_UP


class OpportunityDemandScoreService:
    @staticmethod
    def calculate(demand_score):
        score = Decimal(str(demand_score))
        if not Decimal("0") <= score <= Decimal("100"):
            raise ValueError("Le score de demande doit etre compris entre 0 et 100.")
        points = score * Decimal("30") / Decimal("100")
        return int(points.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
