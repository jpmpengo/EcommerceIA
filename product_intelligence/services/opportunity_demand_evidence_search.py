from pydantic import BaseModel, Field


class DemandEvidence(BaseModel):
    metric: str
    value: str
    source_url: str
    observed_at: str = ""


class DemandEvidenceSearchResponse(BaseModel):
    evidence: list[DemandEvidence] = Field(default_factory=list)


class OpportunityDemandEvidenceSearchService:
    INSTRUCTIONS = """Rechercher uniquement des preuves publiques et verifiables de demande commerciale pour le produit fourni, prioritairement en France. Rechercher des tendances de recherche quantifiees (search_trend) ou une croissance documentee des ventes (sales_growth). Chaque preuve doit comporter une source URL precise et une affirmation fidele a cette source. Pour search_trend, utiliser exclusivement le format anglais X% growth from Month YYYY to Month YYYY, avec X calcule a partir de deux valeurs datees explicitement presentes dans la source. Pour sales_growth, conserver la formulation exacte du produit et du pourcentage documente, de preference en anglais. Ne jamais traduire une approximation en chiffre precis. Ne jamais inventer de volumes, pourcentages ou ventes. Si aucune preuve fiable n existe, retourner evidence vide. Ne pas proposer de nouvelles idees de produits."""

    @classmethod
    def search(cls, idea, model=None):
        from product_intelligence.services.product_idea_generation import ProductIdeaGenerationService
        from product_intelligence.services.openai_client import OpenAIClient
        discovery = ProductIdeaGenerationService._build_discovery_service(model or ProductIdeaGenerationService.DEFAULT_MODEL)
        client = discovery.client
        return client.generate(
            instructions=cls.INSTRUCTIONS,
            context={"product_name": idea.name, "customer_problem": idea.customer_problem, "target_countries": ["FR", "BE", "ES"], "existing_signals": idea.demand_signal_assessments or []},
            response_model=DemandEvidenceSearchResponse,
            use_web_search=True,
        )["evidence"]
