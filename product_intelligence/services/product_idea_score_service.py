from datetime import date


class ProductIdeaScoreService:
    STRENGTH_SCORES = {
        "weak": 25,
        "moderate": 50,
        "strong": 75,
    }

    @classmethod
    def calculate_for_idea(cls, product_idea, reference_date=None, local_saturation=None):
        return cls.calculate(
            product_idea.demand_signal_assessments,
            reference_date=reference_date,
            local_saturation=local_saturation,
        )

    @classmethod
    def calculate(cls, signals, reference_date=None, local_saturation=None):
        reference_date = date.fromisoformat(reference_date) if isinstance(reference_date, str) else reference_date
        if not signals:
            return 0

        scores = []
        for signal in signals:
            score = 0 if signal.get("metric") in ("search_trend", "sales_growth") and signal.get("is_verified") is not True else cls.STRENGTH_SCORES.get(signal.get("strength"), 0)
            type_penalties = {"direct": 0, "trend": 0, "need": 10, "contextual": 20}
            score -= type_penalties.get(signal.get("type"), 0)
            if signal.get("role") == "precursor" and signal.get("metric") == "search_trend" and signal.get("is_verified") is not False and "growth" in str(signal.get("value", "")).lower() and not any(term in str(signal.get("value", "")).lower() for term in ("no growth", "negative growth", "zero growth", "without growth", "declining growth")):
                score += 10
            if signal.get("role") == "precursor":
                market_count = len(set(signal.get("markets") or []))
                score += min(max(market_count - 1, 0) * 5, 15)
            if reference_date and signal.get("observed_at"):
                observed_at = signal["observed_at"]
                if isinstance(observed_at, str):
                    observed_at = date.fromisoformat(observed_at)
                age_days = max((reference_date - observed_at).days, 0)
                if age_days > 90:
                    score -= min((age_days - 90) // 90 * 5 + 5, 25)
            if signal.get("metric") in ("search_trend", "sales_growth") and signal.get("is_verified") is not True:
                score = 0
            scores.append(max(score, 0))

        precursor_scores = [score for signal, score in zip(signals, scores) if signal.get("role") == "precursor"]
        base_score = max(precursor_scores) if precursor_scores else max(scores)

        target_scores = [
            score
            for signal, score in zip(signals, scores)
            if signal.get("role") == "target_market"
        ]

        has_precursor = any(
            signal.get("role") == "precursor"
            for signal in signals
        )

        if has_precursor and target_scores:
            target_bonus = min(max(target_scores) * 25 // 100, 20)
            base_score += target_bonus
        elif not has_precursor:
            base_score = min(base_score, 25)

        saturation_penalties = {
            "low": 0,
            "moderate": 10,
            "high": 20,
        }
        base_score -= saturation_penalties.get(local_saturation, 0)

        return max(min(base_score, 100), 0)
