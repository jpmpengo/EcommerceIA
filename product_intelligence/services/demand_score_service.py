class DemandScoreService:

    SIGNAL_SCORES = {
        "direct": 100,
        "trend": 75,
        "need": 50,
        "contextual": 25,
    }

    @classmethod
    def calculate(cls, signals):
        if not signals:
            return 0

        scores = []

        for signal in signals:
            base_score = cls.SIGNAL_SCORES.get(
                signal.get("type"),
                0,
            )
            role = signal.get("role")

            if role == "precursor":
                base_score = base_score * 50 // 100

            scores.append(base_score)

        scores = sorted(scores, reverse=True)

        if not scores:
            return 0

        score = scores[0]

        for additional_score in scores[1:]:
            score += additional_score * 25 // 100

        return min(score, 100)
