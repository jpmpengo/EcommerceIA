from decimal import Decimal, ROUND_HALF_UP


class OpportunityProfitabilityScoreService:
    THRESHOLDS = [(Decimal("10"), 10), (Decimal("20"), 20), (Decimal("30"), 30), (Decimal("40"), 35), (Decimal("50"), 38), (Decimal("60"), 40)]

    @classmethod
    def calculate(cls, margin_rate):
        margin = Decimal(str(margin_rate))
        if margin < Decimal("10"):
            return 0
        for index in range(1, len(cls.THRESHOLDS)):
            upper_margin, upper_score = cls.THRESHOLDS[index]
            lower_margin, lower_score = cls.THRESHOLDS[index - 1]
            if margin <= upper_margin:
                score = Decimal(lower_score) + (margin - lower_margin) * Decimal(upper_score - lower_score) / (upper_margin - lower_margin)
                return int(score.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return 40
