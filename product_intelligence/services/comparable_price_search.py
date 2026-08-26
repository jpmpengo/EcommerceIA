from pydantic import (
    BaseModel,
    Field,
)


class ComparablePriceResult(BaseModel):

    product_name: str
    observed_price: float = Field(
        gt=0,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    source_title: str

    source_url: str

    evidence: str


class ComparablePriceSearchResponse(BaseModel):

    comparables: list[
        ComparablePriceResult
    ] = Field(
        default_factory=list,
        max_length=5,
    )


class ComparablePriceSearchService:

    MAXIMUM_COMPARABLE_PRICES = 5

    INSTRUCTIONS = """
Tu recherches des prix de vente publics
pour un produit fournisseur précis.

Trouve au maximum cinq produits réellement
comparables vendus au détail.

Un produit comparable doit avoir :

- le même type de produit ;
- la même fonction principale ;
- des dimensions, une capacité ou des
  caractéristiques proches lorsqu'elles sont
  disponibles ;
- un état neuf ;
- un prix actuellement affiché.

Exclus :

- les produits sans rapport ;
- les accessoires destinés à un autre produit ;
- les lots lorsqu'ils ne sont pas comparables ;
- les produits d'occasion ;
- les pages réservées aux grossistes ou aux
  fournisseurs ;
- les résultats dont le prix n'est pas visible ;
- les sources sans URL publique vérifiable.

Pour chaque résultat, fournis :

- le nom exact du produit ;
- le prix affiché ;
- la devise sous forme de code ISO à trois lettres ;
- le titre de la source ;
- l'URL publique de la source ;
- une courte preuve expliquant pourquoi le produit
  est comparable.

N'invente jamais un prix, une caractéristique,
une source ou une URL.

Si aucun produit suffisamment comparable n'est
trouvé, retourne une liste vide.
"""

    def __init__(
        self,
        client,
    ):
        self.client = client

    def search(
        self,
        supplier_offer,
    ):
        product_idea = (
            supplier_offer.product_idea
        )

        category_name = ""
        target_countries = []

        if product_idea is not None:
            category_name = (
                product_idea.name
            )

            target_countries = (
                product_idea.countries
                or []
            )

        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={
                "maximum_comparable_prices": (
                    self.MAXIMUM_COMPARABLE_PRICES
                ),
                "supplier_product": {
                    "name": (
                        supplier_offer.product_name
                    ),
                    "variant_features": (
                        supplier_offer.variant_features
                        or {}
                    ),
                },
                "category": {
                    "name": category_name,
                    "target_countries": (
                        target_countries
                    ),
                },
                "rules": {
                    "retail_products_only": True,
                    "new_products_only": True,
                    "visible_price_required": True,
                    "public_source_required": True,
                },
            },
            response_model=(
                ComparablePriceSearchResponse
            ),
            use_web_search=True,
        )