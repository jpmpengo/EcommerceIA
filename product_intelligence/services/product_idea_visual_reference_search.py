from pydantic import BaseModel, Field, ValidationInfo, model_validator


class ProductIdeaVisualReferenceSearchResult(BaseModel):
    supplier_search_keyword: str
    product_name: str
    source_title: str
    source_url: str
    image_url: str


class ProductIdeaVisualReferenceSearchResponse(BaseModel):
    visual_references: list[
        ProductIdeaVisualReferenceSearchResult
    ] = Field(
        default_factory=list,
        max_length=15,
    )

    @model_validator(mode="after")
    def validate_keyword_coverage(self, info: ValidationInfo):
        expected = set((info.context or {}).get("supplier_search_keywords") or [])
        actual = {r.supplier_search_keyword for r in self.visual_references}
        if expected and expected != actual:
            raise ValueError("Chaque mot-cle fournisseur doit avoir une reference visuelle.")
        return self


class ProductIdeaVisualReferenceSearchService:

    INSTRUCTIONS = """
Tu recherches des references visuelles publiques
pour les mots-cles fournisseur d une idee produit.

Pour chaque mot-cle fournisseur :
- trouve au moins une image representant precisement le produit recherche ;
- utilise une source publique independante des fournisseurs qui seront recherches ensuite ;
- fournis le nom du produit ;
- fournis le titre de la source ;
- fournis l URL publique de la page ;
- fournis l URL HTTPS directe de l image ;
- n invente jamais une URL, une image ou une source.
"""

    def __init__(self, client):
        self.client = client

    def search(self, product_idea):
        result = self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={
                "product_idea_name": product_idea.name,
                "supplier_search_keywords": (
                    product_idea.supplier_search_keywords
                ),
            },
            response_model=(
                ProductIdeaVisualReferenceSearchResponse
            ),
            use_web_search=True,
        )

        validated = ProductIdeaVisualReferenceSearchResponse.model_validate(
            result,
            context={
                "supplier_search_keywords": product_idea.supplier_search_keywords,
            },
        )
        return validated.model_dump()
