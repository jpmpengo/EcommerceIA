class CompetitionScoreService:

    MINIMUM_COMPARABLE_PRICES = 3
    MINIMUM_SOURCE_DOMAINS = 2

    @classmethod
    def calculate(cls, market_summary):
        if (
            market_summary.get("retained_count", 0) < cls.MINIMUM_COMPARABLE_PRICES
            or market_summary.get("source_domain_count", 0) < cls.MINIMUM_SOURCE_DOMAINS
        ):
            return 0

        source_domain_count = market_summary.get("source_domain_count", 0)
        score = min((source_domain_count - 1) * 25, 100)

        minimum_price = market_summary.get("minimum_price")
        median_price = market_summary.get("median_price")
        maximum_price = market_summary.get("maximum_price")

        if (
            minimum_price is None
            or median_price is None
            or maximum_price is None
            or median_price <= 0
        ):
            return score

        dispersion = (
            maximum_price - minimum_price
        ) / median_price

        if dispersion <= 0.25:
            return score

        if dispersion <= 0.75:
            return score * 75 // 100

        return score * 50 // 100
