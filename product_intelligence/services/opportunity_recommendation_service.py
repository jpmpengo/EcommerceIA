


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
        additional_instructions=None,
    ):
        if score_data.get("analysis_complete") is False:
            blockers = []
            if score_data.get("missing_competition"):
                blockers.append({"category": "competition", "blocker": "Saturation concurrentielle indeterminee", "research_action": "Completer les preuves de saturation concurrentielle", "resolution_criterion": "Saturation documentee avec des preuves suffisantes"})
            if score_data.get("missing_demand"):
                blockers.append({"category": "demand", "blocker": "Demande insuffisamment documentee", "research_action": "Completer les preuves de demande", "resolution_criterion": "Demande suffisamment documentee pour permettre une recommandation"})
            if not blockers:
                blockers.append({"category": "other", "blocker": "Analyse commerciale incomplete", "research_action": "Identifier et completer les informations manquantes", "resolution_criterion": "Analyse commerciale complete"})
            return {"decision": "study", "study_blockers": blockers, "summary": "Analyse incomplete : des recherches complementaires sont necessaires avant recommandation."}

        context = {
            "product": product_data,
            "score": score_data["score"],
            "reasons": score_data["reasons"],
        }

        result = self.engine.recommend(context, additional_instructions=additional_instructions) if additional_instructions else self.engine.recommend(context)

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

            