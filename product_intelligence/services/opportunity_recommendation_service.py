


class OpportunityRecommendationService:

    REQUIRED_RESPONSE_FIELDS = {
        "decision",
        "summary",
    }

    ALLOWED_DECISIONS = {
        "study",
        "recommend",
        "reject",
    }

    def __init__(self, engine):
        self.engine = engine

    def recommend(
        self,
        product_data,
        score_data,
    ):
        context = {
            "product": product_data,
            "score": score_data["score"],
            "reasons": score_data["reasons"],
        }

        result = self.engine.recommend(
            context
        )

        self._validate_response(
            result
        )

        return result

    @classmethod
    def _validate_response(cls, result):
        if not isinstance(result, dict):
            raise ValueError(
                "La réponse du moteur IA doit être un dictionnaire."
            )

        missing_fields = (
            cls.REQUIRED_RESPONSE_FIELDS
            - set(result.keys())
        )

        if missing_fields:
            raise ValueError(
                (
                    "Réponse IA invalide. "
                    "Champs manquants : "
                    f"{sorted(missing_fields)}"
                )
            )

        decision = result["decision"]
        summary = result["summary"]

        if not decision:
            raise ValueError(
                "La décision IA est obligatoire."
            )

        if decision not in cls.ALLOWED_DECISIONS:
            raise ValueError(
                (
                    "Décision IA invalide : "
                    f"{decision}"
                )
            )

        if not summary:
            raise ValueError(
                "Le résumé IA est obligatoire."
            )

            