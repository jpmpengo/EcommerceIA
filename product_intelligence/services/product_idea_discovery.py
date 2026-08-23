from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


CountryCode = Literal[
    "FR",
    "BE",
    "ES",
]


class ProductIdea(BaseModel):
    name: str
    customer_problem: str
    target_customer: str
    reason_to_study: str

    countries: list[CountryCode] = Field(
        min_length=1,
        max_length=3,
    )

    search_keywords: list[str] = Field(
        min_length=1,
        max_length=5,
    )


class ProductDiscoveryResponse(BaseModel):
    ideas: list[ProductIdea] = Field(
        min_length=5,
        max_length=5,
    )


class ProductIdeaDiscoveryService:

    INSTRUCTIONS = """
Tu participes à la découverte de produits
pour EcommerceIA.

Propose exactement cinq hypothèses de produits
à étudier pour les marchés indiqués.

Ces idées ne sont pas des recommandations
d'achat ni des affirmations sur les meilleures
ventes actuelles.

Pour chaque idée :

- décris précisément le produit ;
- indique le problème client auquel il répond ;
- indique le client cible ;
- explique pourquoi l'idée mérite une étude ;
- indique les pays concernés ;
- fournis des mots-clés adaptés à une future
  recherche ciblée sur les marketplaces.

N'invente aucun chiffre de vente, prix, volume
ou part de marché.

Les pays autorisés sont uniquement :

- FR pour la France ;
- BE pour la Belgique ;
- ES pour l'Espagne.
"""

    TARGET_COUNTRIES = [
        "FR",
        "BE",
        "ES",
    ]

    MAXIMUM_IDEAS = 5

    def __init__(
        self,
        client,
    ):
        self.client = client

    def discover(self):
        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={
                "maximum_ideas": (
                    self.MAXIMUM_IDEAS
                ),
                "target_countries": (
                    self.TARGET_COUNTRIES
                ),
                "objective": (
                    "Identifier une courte liste "
                    "d'idées à valider ensuite "
                    "avec des données externes."
                ),
            },
            response_model=(
                ProductDiscoveryResponse
            ),
        )
