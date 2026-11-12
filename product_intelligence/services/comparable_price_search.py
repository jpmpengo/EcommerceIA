from pydantic import (
    BaseModel,
    Field,
)

from product_intelligence.services.product_comparability_attributes import (
    ProductComparabilityAttributesService,
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

    image_url: str | None = None

    shipping_days_min: int | None = Field(default=None, ge=0)
    shipping_days_max: int | None = Field(default=None, ge=0)
    shipping_cost: float | None = Field(default=None, ge=0)
    shipping_currency: str | None = None
    free_shipping: bool | None = None
    shipping_destination_country: str | None = None
    shipping_evidence: str | None = None

    commercial_segment: str = "unclassified"
    commercial_segment_reason: str | None = None

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
- les produits dont le nombre d'unités diffère ;
- les variantes dont la taille, les dimensions ou
  la capacité diffèrent ;
- les produits d'occasion ;
- les pages réservées aux grossistes ou aux
  fournisseurs ;
- les résultats dont le prix n'est pas visible ;
- les sources sans URL publique vérifiable.

Recherche les prix sur les marches cibles indiques dans category.target_countries (FR, BE, ES selon le produit).
Verifie que chaque offre est commercialisee pour au moins un pays cible.
Un domaine etranger ne prouve pas a lui seul que le produit est indisponible sur ces marches.
Ne retiens pas les offres uniquement destinees a des marches exterieurs.
Si les offres locales verifiables sont insuffisantes, retourne moins de comparables plutot que des offres hors marche.

Utilise la description technique du fournisseur (supplier_product.product_description) pour identifier les fonctions essentielles du produit.
Recherche prioritairement des offres possedant ces memes fonctions essentielles et un positionnement commercial equivalent.
Ne confonds pas une ressemblance de nom, de categorie ou d apparence avec une equivalence fonctionnelle.
Une fonction essentielle absente ou contradictoire doit conduire a ecarter le candidat de la recherche directe.
N invente pas de caracteristiques absentes de la description fournisseur ou des sources publiques.
Si aucun produit directement equivalent n est verifiable, retourne moins de resultats, voire aucun.

Chaque comparable doit provenir d une fiche produit individuelle accessible par son URL exacte.
Verifie que le nom du produit et son prix correspondent a cette fiche precise.
Exclus les pages de recherche, les pages de categorie, les listes de produits et les pages d accueil.
Ne fournis jamais un prix attribue a une fiche lorsque la source ne permet pas de le verifier.
Si la fiche exacte est introuvable, ne retiens pas ce comparable.

Diversifie les sources :
- recherche des produits comparables sur plusieurs domaines distincts ;
- vise au moins trois domaines distincts lorsque cela est possible ;
- évite de retourner plusieurs résultats du même domaine tant qu un autre domaine public et vérifiable propose un produit réellement comparable.

Pour chaque résultat, fournis :

- le nom exact du produit ;
- le prix affiché ;
- la devise sous forme de code ISO à trois lettres ;
- le titre de la source ;
- l'URL publique de la source ;
- fournis image_url avec une URL HTTPS directe vers l image principale du produit lorsqu elle est publiquement verifiable ; sinon null ;
- une courte preuve expliquant pourquoi le produit
  est comparable, en citant explicitement le nombre
  d'unités, la taille, les dimensions et la capacité
  lorsqu'ils sont disponibles.

N'invente jamais un prix, une caractéristique,
une source ou une URL.

Si aucun produit suffisamment comparable n'est
trouvé, retourne une liste vide.
"""

    INSTRUCTIONS += """
Pour chaque produit comparable, recherche aussi les conditions de livraison publiquement affichees.
Renseigne shipping_days_min et shipping_days_max uniquement si un delai en jours est explicitement annonce pour le pays de destination.
Renseigne shipping_cost et shipping_currency uniquement si les frais de livraison sont explicitement affiches.
Renseigne free_shipping uniquement si la gratuite ou le caractere payant de la livraison est clairement etabli.
Renseigne shipping_destination_country avec le code FR, BE ou ES correspondant aux informations verifiees.
Renseigne shipping_evidence avec la preuve textuelle de livraison et sa provenance.
Si les informations de livraison sont absentes, ambiguës ou dependent du panier ou de l adresse, utilise null pour les champs concernes.
Ne deduis jamais les delais ou les frais de livraison du pays du vendeur, de la plateforme ou du prix du produit.
La livraison inconnue ne doit pas exclure un produit dont le prix et la comparabilite sont verifies.
"""

    INSTRUCTIONS += """
Pour chaque comparable, renseigne commercial_segment : direct, different_segment ou unclassified.
Renseigne commercial_segment_reason avec une justification fondee sur des caracteristiques verifiables : fonctionnalites, materiaux, marque et positionnement documente.
Classe direct si le produit appartient a la meme gamme commerciale que le produit fournisseur.
Classe different_segment uniquement si des preuves etablissent une gamme commerciale distincte.
Ne classe jamais different_segment sur le prix seul.
Si les preuves sont insuffisantes, utilise unclassified et explique pourquoi.
Conserve les produits premium fonctionnellement comparables dans les resultats.
"""

    INSTRUCTIONS += """
Lorsque study_blockers contient des blocages relatifs aux prix comparables, utilise leurs research_action et resolution_criterion pour orienter prioritairement la recherche.
Recherche uniquement des preuves verifiables permettant de resoudre ces blocages, en respectant les caracteristiques essentielles du produit fournisseur.
Ne refais pas inutilement les verifications deja fiables et ne considere jamais un blocage resolu sans preuve suffisante.
Si les recherches complementaires ne donnent aucun resultat fiable, retourne une liste vide plutot que des comparables artificiels.
"""

    def __init__(
        self,
        client,
    ):
        self.client = client

    def search(
        self,
        supplier_offer,
        study_blockers=None,
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

        attributes = ProductComparabilityAttributesService().extract(
            name=supplier_offer.product_name,
            persisted_features=(supplier_offer.variant_features or {}),
        )

        return self.client.generate(
            instructions=self.INSTRUCTIONS,
            context={
                "study_blockers": study_blockers or [],
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
                    "comparability_attributes": attributes,
                    "product_description": supplier_offer.product_description or "",
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
