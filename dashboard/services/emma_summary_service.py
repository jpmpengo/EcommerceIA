from dashboard.services.emma_state_service import EmmaState


class EmmaSummaryService:

    @staticmethod
    def build(state):
        if state == EmmaState.ACTION_REQUIRED:
            return {
                "title": "Votre attention est requise",
                "message": (
                    "Voici l'action que je vous conseille "
                    "de traiter maintenant."
                ),
            }

        if state == EmmaState.PREPARATION_REQUIRED:
            return {
                "title": "Des produits restent à préparer",
                "message": (
                    "Toutes les opportunités prêtes ont été traitées. "
                    "Il reste cependant quelques produits à préparer "
                    "avant leur publication."
                ),
            }
   
        return {
            "title": "Tout est sous contrôle",
            "message": (
                "Toutes les opportunités prêtes ont été traitées."
            ),
        }


        