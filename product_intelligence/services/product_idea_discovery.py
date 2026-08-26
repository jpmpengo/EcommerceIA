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


class EvidenceSource(BaseModel):
    title: str
    url: str
    evidence: str


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

    supplier_search_keywords: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    demand_signals: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    evidence_sources: list[
        EvidenceSource
    ] = Field(
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
Tu participes à la découverte de catégories
de produits pour EcommerceIA.

Utilise la recherche Web et propose exactement
cinq catégories de produits qui semblent
prometteuses dans les pays indiqués.

Une catégorie doit être suffisamment précise
pour permettre ensuite une recherche dans les
catalogues de plusieurs fournisseurs.

Pour chaque catégorie :

- donne un nom précis et compréhensible ;
- décris le problème client auquel elle répond ;
- indique le client cible ;
- explique pourquoi elle mérite une étude ;
- indique les pays concernés ;
- fournis des mots-clés adaptés à une recherche
  future auprès des fournisseurs et sur le Web ;
- fournis séparément entre un et cinq mots-clés
  fournisseur en anglais, précis et adaptés aux
  catalogues internationaux;
- présente entre un et cinq signaux de demande ;
- fournis entre une et cinq sources publiques ;
- indique pour chaque source son titre, son URL
  et ce qu’elle permet réellement d’établir.

Les sources doivent être accessibles publiquement
et directement liées aux signaux présentés.

Ne présente jamais une catégorie comme une
meilleure vente certaine si les sources ne le
démontrent pas explicitement.

N’invente aucun chiffre de vente, prix, volume,
stock, délai, coût de livraison ou part de marché.

Distingue clairement les faits sourcés des
hypothèses qui devront encore être validées avec
les fournisseurs et les prix comparables.

Les pays autorisés sont uniquement :

- FR pour la France ;
- BE pour la Belgique ;
- ES pour l’Espagne.
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

    def discover(
        self,
    ):
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
                    "Identifier exactement cinq "
                    "catégories de produits "
                    "prometteuses, appuyées par "
                    "des signaux de demande et "
                    "des sources publiques."
                ),
            },
            response_model=(
                ProductDiscoveryResponse
            ),
            use_web_search=True,
        )