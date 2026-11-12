from pydantic import BaseModel, Field


class ComparableLogisticsResult(BaseModel):
    comparable_id: int
    shipping_days_min: int | None = Field(default=None, ge=0)
    shipping_days_max: int | None = Field(default=None, ge=0)
    shipping_cost: float | None = Field(default=None, ge=0)
    shipping_currency: str | None = None
    free_shipping: bool | None = None
    shipping_destination_country: str | None = None
    shipping_evidence: str | None = None


class ComparableLogisticsResponse(BaseModel):
    results: list[ComparableLogisticsResult] = Field(default_factory=list)


class ComparablePriceLogisticsSearchService:
    INSTRUCTIONS = """Recherche exclusivement les conditions de livraison des produits fournis dans le contexte. Utilise les URL exactes des fiches produits et, si necessaire, les pages officielles de livraison du meme marchand. Ne recherche pas de nouveaux produits et ne modifie aucun prix. Pour chaque comparable, conserve exactement son comparable_id. Recherche les delais de livraison au client, les frais, la devise et la gratuite eventuelle pour le pays de destination indique. Fournis shipping_evidence avec la source URL et la preuve textuelle verifiable. Ne confonds pas expedition et livraison au client. Ne deduis jamais un delai ou un tarif du pays du marchand. Si une information est absente, ambiguë ou depend du panier ou de l adresse, retourne null. Ne fournis aucun resultat sans preuve logistique verifiable."""

    def __init__(self, client):
        self.client = client

    def search(self, comparables, destination_country="FR"):
        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={"destination_country": destination_country, "comparables": [{"comparable_id": c.id, "product_name": c.product_name, "source_url": c.source_url} for c in comparables]},
            response_model=ComparableLogisticsResponse,
            use_web_search=True,
        )
