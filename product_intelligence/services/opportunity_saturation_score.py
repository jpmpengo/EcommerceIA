class OpportunitySaturationScoreService:
    SCORES = {
        "very_low": 30,
        "low": 24,
        "moderate": 18,
        "high": 9,
        "very_high": 0,
        "indeterminate": None,
    }

    @classmethod
    def calculate(cls, level):
        if level not in cls.SCORES:
            raise ValueError("Niveau de saturation inconnu.")
        return cls.SCORES[level]
