class AIRecommendationEngine:

    INSTRUCTIONS = """
Tu es le moteur d'analyse commerciale d'EcommerceIA.

À partir du contexte fourni, retourne une recommandation structurée.

La décision doit être strictement l'une des valeurs suivantes :
- study
- recommend
- reject

La réponse doit contenir :
- decision
- summary

Ne retourne pas d'autre statut.
"""

    def __init__(self, client):
        self.client = client

    def recommend(self, context):
        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context=context,
        )
        