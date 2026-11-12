from dashboard.services.emma_state_service import EmmaState


class EmmaSummaryService:

    @staticmethod
    def build(state):
        if state == EmmaState.REVIEW_REQUIRED:
            return {
                "title": "Des opportunites sont pretes a etre examinees",
                "message": (
                    "Les assistants ont prepare des opportunites "
                    "qui attendent maintenant votre examen."
                ),
            }

        return {
            "title": "Aucune opportunite a examiner",
            "message": (
                "Aucune opportunite produite par les assistants "
                "n attend actuellement votre examen."
            ),
        }
