from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    HttpUrl,
    field_validator,
    Field,
    model_validator,
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


class CompetitorDeliveryEvidence(BaseModel):
    competitor_product_name: str = ""
    status: Literal["verified_comparable", "verified_short", "unknown"] = "unknown"
    country: CountryCode
    delivery_days_min: int | None = Field(default=None, ge=0)
    delivery_days_max: int | None = Field(default=None, ge=0)
    source_url: str | None = None

    @model_validator(mode="after")
    def validate_delivery_evidence(self):
        if self.status != "unknown":
            if self.delivery_days_min is None or self.delivery_days_max is None or not self.source_url:
                self.status = "unknown"
                return self
            HttpUrl(self.source_url)
            if self.delivery_days_min > self.delivery_days_max:
                raise ValueError("Plage de livraison incoherente.")
            if self.status == "verified_short" and self.delivery_days_max >= 15:
                self.status = "unknown"
        return self


class DemandSignalAssessment(BaseModel):
    type: Literal[
        "direct",
        "trend",
        "need",
        "contextual",
    ]

    markets: list[str] = Field(
        min_length=1,
    )

    role: Literal[
        "precursor",
        "target_market",
    ]

    strength: Literal["weak", "moderate", "strong"]

    metric: str
    value: str
    source_url: str
    observed_at: date


    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value):
        HttpUrl(value)
        return value

class ProductIdeaVisualReference(BaseModel):
    supplier_search_keyword: str
    product_name: str
    source_title: str
    source_url: str
    image_url: str

class ProductIdea(BaseModel):
    name: str

    category_path: list[str] = Field(
        min_length=3,
        max_length=3,
    )

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

    class LocalizedSupplierKeyword(BaseModel):
        supplier_search_keyword: str
        FR: str
        BE: str
        ES: str

    supplier_search_keywords_localized: list[LocalizedSupplierKeyword] = Field(
        min_length=1,
        max_length=5,
    )

    visual_references: list[
        ProductIdeaVisualReference
    ] = Field(
        min_length=1,
        max_length=15,
    )

    demand_signals: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    demand_signal_assessments: list[
        DemandSignalAssessment
    ] = Field(
        min_length=1,
        max_length=5,
    )

    evidence_sources: list[
        EvidenceSource
    ] = Field(
        min_length=1,
        max_length=5,
    )

    competitor_delivery_evidence: list[CompetitorDeliveryEvidence] = Field(default_factory=list)


    @model_validator(mode="after")
    def validate_precursor_signal(self):
        if not any(
            assessment.role == "precursor"
            and assessment.type in ("direct", "trend")
            and assessment.strength in ("moderate", "strong")
            for assessment in self.demand_signal_assessments
        ):
            raise ValueError(
                "Chaque idee retenue doit avoir au moins un signal precursor."
            )

        return self

    @model_validator(mode="after")
    def validate_visual_references(self):
        supplier_keywords = set(
            self.supplier_search_keywords
        )
        reference_keywords = {
            reference.supplier_search_keyword
            for reference in self.visual_references
        }

        if not supplier_keywords.issubset(reference_keywords):
            raise ValueError(
                "Chaque mot-cle fournisseur doit avoir "
                "au moins une reference visuelle associee."
            )

        return self

class ProductDiscoveryResponse(BaseModel):
    ideas: list[ProductIdea] = Field(
        min_length=0,
        max_length=5,
    )


class ProductIdeaDiscoveryService:

    INSTRUCTIONS = """
HISTORIQUE ET NON-REPETITION :
Le contexte previous_ideas contient les produits deja etudies par EcommerceIA, quel que soit leur statut, avec name, supplier_search_keywords, category_path, customer_problem et reason_to_study.
Compare chaque nouveau candidat aux produits historiques selon sa fonction principale, son mode de fonctionnement, ses caracteristiques et le probleme client resolu.
Deux produits qui repondent au meme besoin ne sont pas necessairement identiques : distingue leurs solutions concretes.
Une nouvelle preuve de demande, un nouveau concurrent ou un nouveau delai de livraison ne constitue pas une innovation fonctionnelle.
Si une amelioration fonctionnelle justifie une nouvelle etude, identifie le produit historique concerne, explique la difference concrete et cite une source publique verifiable dans les preuves du candidat.
Consulte cet historique avant de retenir une nouvelle idee.
Ne repropose pas un produit identique ou fonctionnellement equivalent sous un autre nom, une traduction ou une reformulation.
Une variante est admissible uniquement si elle apporte une amelioration fonctionnelle concrete, documentee par une source publique et susceptible de modifier son interet commercial.
Dans ce cas, explique explicitement cette amelioration dans reason_to_study.
Ne considere pas un changement de couleur, de taille, de presentation ou de formulation comme une innovation suffisante.
Si les candidats nouveaux sont insuffisants, retourne moins de cinq idees plutot que de recycler des produits historiques.

Pour chaque observation competitor_delivery_evidence, renseigne competitor_product_name avec le nom exact du produit concurrent identifie sur la page source. Ne deduis pas ce nom du produit EcommerceIA et ne l invente jamais. Si le nom du produit concurrent ne peut pas etre identifie, utilise une chaine vide. Une source de delai sans correspondance produit explicite ne constitue pas une preuve logistique pleinement verifiee.

Tu participes à la découverte de catégories
de produits pour EcommerceIA.

Utilise la recherche Web comme un radar commercial.

US, JP et KR prioritaires : recherche en priorite les tendances emergentes aux Etats-Unis, au Japon et en Coree du Sud.
Les autres marches autorises restent des sources possibles de tendances si les preuves sont solides, sans quota geographique obligatoire.
Pour chaque candidat, recherche une preuve d emergence recente : croissance documentee, nouvel usage ou innovation identifiable. La simple existence du produit ne suffit pas.
Recherche une differenciation sur FR/BE/ES : nouveaute fonctionnelle, variante innovante ou presence commerciale encore limitee. Ne confonds pas cette verification preliminaire avec l analyse detaillee de saturation realisee ensuite.
Compatibilite avec le modele EcommerceIA : approvisionnement principalement depuis la Chine, avec des delais de livraison pouvant atteindre 15 a 25 jours.
Privilegie les produits emergents avec une forte demande potentielle, une faible presence commerciale sur FR/BE/ES et une differenciation rendant ce delai acceptable.
Cette orientation reste preliminaire : la saturation, les couts, la rentabilite et les delais reels seront verifies par les services specialises EcommerceIA.

Recherche à la fois la demande confirmée sur FR/BE/ES et les signaux relevant d un radar précurseur international.
Observe plusieurs catégories candidates avant de sélectionner au maximum cinq catégories pour étude commerciale.
Diversifie les idees finales entre plusieurs familles commerciales reelles (maison, cuisine, animaux, jardin, loisirs, bien-etre, accessoires pratiques ou autres). Ne retiens jamais plus de deux idees appartenant a une meme famille commerciale, meme si leurs noms ou sous-categories different. Vise au moins trois familles distinctes. Ne sacrifie pas la qualite des preuves et n invente pas de tendances pour respecter cette diversification.
Compare les candidats sans quota géographique et sans ordre géographique : un signal précurseur international solide peut être retenu même si la demande n est pas encore confirmée sur FR/BE/ES.
Distingue toujours un signal précurseur international d une preuve de demande confirmée sur FR/BE/ES.

Une catégorie doit être suffisamment précise
pour permettre ensuite une recherche dans les
catalogues de plusieurs fournisseurs.

Pour chaque catégorie :

- donne un nom précis et compréhensible ;
- fournis category_path avec exactement trois niveaux hierarchiques, du plus general au plus precis ;
- décris le problème client auquel elle répond ;
- indique le client cible ;
- explique pourquoi elle mérite une étude ;
- indique les pays concernés ;
- fournis des mots-clés adaptés à une recherche
  future auprès des fournisseurs et sur le Web ;
- fournis séparément entre un et cinq mots-clés
  fournisseur en anglais, précis et adaptés aux
  catalogues internationaux;
- conserve ces supplier_search_keywords en anglais comme référence canonique pour les catalogues internationaux, notamment EPROLO et CJ CN ;
 - fournis aussi supplier_search_keywords_localized : pour chaque mot-cle fournisseur anglais, fournis une variante de recherche locale en FR (francais), BE (francais ou neerlandais selon le contexte) et ES (espagnol), sans remplacer le mot-cle anglais canonique ;
- fournis des images associées à chaque mot-clé fournisseur ;
- pour chaque supplier_search_keywords, fournis au moins une entree dans visual_references dont supplier_search_keyword reprend exactement le mot-cle anglais canonique, caractere pour caractere, sans traduction, ajout ni reformulation ;
- chaque image doit représenter précisément le produit recherché par ce mot-clé ;
- les images doivent provenir de sources publiques indépendantes des fournisseurs qui seront recherchés ensuite ;
- pour chaque image, fournis le nom du produit, le titre de la source, l URL publique de la page et l URL HTTPS directe de l image ;
- n invente jamais une URL d image ;
- présente entre un et cinq signaux de demande ;
- pour chaque signal, fournis aussi demand_signal_assessment avec :
  type : direct, trend, need ou contextual ;
  markets : la liste des marchés où ce signal a réellement été observé ; privilégie les codes des pays réellement identifiables dans les sources (par exemple US, JP, KR) ; utilise International uniquement lorsque les sources ne permettent pas une attribution géographique plus précise ;
  role : target_market si le signal concerne directement FR/BE/ES, ou precursor s il s agit d un signal précurseur international ;
- pour chaque idee retenue, fournis au moins un signal precursor appuye par une source publique ; les signaux target_market servent a confirmer le potentiel local mais ne remplacent pas ce signal precursor ;
  strength : classer la force du signal selon les preuves observees : weak pour un indice indirect ou limite, moderate pour un signal concret mais de portee ou de preuve limitee, strong pour un signal direct et solidement etaye par les elements publics observes ;
  metric : le nom de l indicateur public effectivement observe (par exemple sales, reviews, ranking, search_trend ou adoption) ;
  value : la valeur ou le constat publie par la source, sans inventer ni estimer une valeur absente ;
  source_url : l URL publique precise qui permet de verifier cet indicateur ;
  observed_at : une date ISO obligatoire au format YYYY-MM-DD ; si seule une annee est connue, utilise YYYY-12-31 ; si seul un mois est connu, utilise le dernier jour de ce mois ; si la source donne une periode, utilise la date de fin de cette periode ; n invente jamais une precision temporelle absente de la source ;
- qualifie chaque signal avec un type parmi :
  direct : preuve directement liée à un usage, un achat ou une pratique mesurée ;
  trend : évolution documentée dans le temps ;
  need : besoin, problème ou attente utilisateur documenté ;
  contextual : contexte favorable sans preuve directe de demande commerciale ;
- pour chaque idee, renseigne competitor_delivery_evidence avec les observations de livraison concurrente sur FR, BE ou ES ;
- utilise status verified_comparable pour un delai concurrent annonce publiquement de 15 jours ou plus, sans plafond de duree ;
- utilise status verified_short pour un delai annonce publiquement et plus court que cette reference ;
- utilise status unknown lorsque le delai concurrent ne peut pas etre documente ;
- pour chaque delai documente, fournis country, delivery_days_min, delivery_days_max et source_url correspondant a la page publique exacte ;
- ne classe jamais un delai comme verifie sur la seule base du pays d expedition suppose, du type de fournisseur ou de la tolerance presumee du client ;
- ne fabrique aucun delai ni aucune URL ;
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

Preferences supplementaires de selection :
- CONDITION OBLIGATOIRE DE SELECTION : ne retiens une idee que si au moins une offre concurrente reellement comparable en FR, BE ou ES annonce publiquement un delai minimum de livraison strictement superieur a 7 jours, avec une URL source verifiable. Une plage de 2 a 10 jours ne satisfait pas cette condition. Si aucune idee ne satisfait cette condition, retourne zero idee.
- Exclue les produits necessitant une personnalisation par saisie client ; les variantes predefinies restent admissibles.

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
        previous_ideas=None,
    ):
        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={
                "previous_ideas": previous_ideas or [],
                "maximum_ideas": (
                    self.MAXIMUM_IDEAS
                ),
                "target_countries": (
                    self.TARGET_COUNTRIES
                ),
                "objective": (
                    "Identifier au maximum cinq catégories à étudier commercialement "
                    "après comparaison de la demande documentée sur FR/BE/ES et des "
                    "signaux de radar précurseur international, appuyés par des sources publiques."
                ),
            },
            response_model=(
                ProductDiscoveryResponse
            ),
            use_web_search=True,
        )