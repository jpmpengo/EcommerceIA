# Architecture d'EcommerceIA

## Objectif

Ce document décrit les responsabilités techniques durables du système. Les
détails métier appartiennent à `BUSINESS.md` et la stratégie d'entrée produit à
`PRODUCT_DISCOVERY.md`.

## Principe général

```text
Observer
  -> comprendre
  -> conseiller
  -> décider
  -> exécuter
```

Les données observées ne doivent pas commander directement une action. Elles
sont normalisées, analysées et présentées avant toute décision irréversible.

## Architecture fonctionnelle cible

```text
Signaux publics sourcés
  -> cinq catégories prometteuses
  -> produits et offres fournisseur
  -> préqualification fournisseur
  -> recherche de prix comparables
  -> observations concurrentielles
  -> calcul des indicateurs et des scores
  -> opportunités
  -> validation humaine par Emma
  -> catalogue
  -> commande client
  -> paiement
  -> approvisionnement
  -> expédition et suivi
```

Une catégorie proposée, une offre fournisseur, une observation de prix, une
opportunité, un produit publié et une commande client sont des objets distincts.
Ils ne doivent jamais être confondus.

Le parcours de découverte ne dépend pas d'une connexion directe à une
marketplace. Les prix comparables sont obtenus par une recherche web limitée,
sourcée et datée.

## Domaines du projet

### Boutique

Les applications orientées client présentent le catalogue et exécutent le
parcours d'achat :

- `core` : structure générale et accueil public ;
- `products` : catalogue et fiches produit ;
- `cart` : panier de session ;
- `orders` : commandes, réservations, paiement et suivi ;
- `accounts` : inscription et authentification.

### Intelligence produit

`product_intelligence` collecte, normalise et analyse les informations
nécessaires à l'étude des catégories et des produits :

- découverte de catégories prometteuses ;
- recherche et synthèse de signaux publics sourcés ;
- clients et Providers fournisseurs ;
- produits et offres fournisseur ;
- préqualification selon le prix, le stock et la livraison ;
- recherche web de prix comparables ;
- observations concurrentielles datées et sourcées ;
- extraction des caractéristiques ;
- rapprochement et comparaison des produits ;
- conversion des devises ;
- estimation du coût livré ;
- calcul des marges et des scores ;
- qualification et création d'opportunités.

Les anciennes intégrations directes aux marketplaces ne font plus partie de
l'architecture fonctionnelle cible.

### Décision commerciale

`dashboard` et `recommendations` constituent l'espace de travail du commerçant :

- observation de la situation ;
- présentation des priorités ;
- analyse d'une opportunité ;
- explication des recommandations ;
- approbation, report ou rejet ;
- publication contrôlée.

Django Admin reste un outil technique de maintenance et de correction des
données. Il n'est pas l'interface métier principale.

## Catégories de composants

### Clients et Providers

Ils communiquent avec les systèmes externes et isolent leurs protocoles. Le
reste du domaine ne doit pas dépendre directement du format d'une API ou d'un
fournisseur particulier.

Les Providers fournisseurs fournissent notamment les prix d'achat, les stocks,
les variantes, les délais et les frais de livraison disponibles.

### Importers et Searchers

Les Importers transforment les réponses des fournisseurs en données métier
normalisées.

Les Searchers effectuent des recherches ciblées et limitées dans des sources
autorisées, notamment la recherche web. Ils conservent l'URL, la date et les
informations nécessaires pour justifier chaque observation.

Ni un Importer ni un Searcher ne doit créer directement une opportunité.

### Services

Un service porte une seule responsabilité métier. Il reçoit des données
explicites et retourne un résultat exploitable sans décider de sa présentation.

Exemples historiques :

- `OpportunityAnalyzer` calcule les indicateurs d'une opportunité ;
- `OpportunityAdvisor` transforme ces indicateurs en explication ;
- `RecommendationDecisionService` applique une décision du commerçant ;
- `OpportunityPublisher` transforme une opportunité validée en produit ;
- `OrderReservationService` calcule et protège le stock réservé ;
- `OrderPaymentService` confirme un paiement de manière idempotente.

### Advisors

Un Advisor est créé lorsqu'un domaine nécessite une interprétation ou une
recommandation explicable. Il ne doit pas exécuter l'action recommandée.

### Executors

Un Executor applique une décision déjà prise. Il ne décide pas pourquoi cette
action est souhaitable.

### Vues et templates

Les vues orchestrent les entrées HTTP, les services et les réponses. Les
templates présentent les données sans porter de règles métier.

## Frontières de responsabilité

- Une vue ne contient pas de calcul métier complexe.
- Un modèle conserve l'état et les invariants proches de ses données.
- Un template n'autorise ni ne refuse une action métier.
- Un service ne doit pas connaître l'interface qui affichera son résultat.
- Un Advisor explique sans publier.
- Un Publisher publie sans recalculer la justification commerciale.
- Un client API ne crée pas directement une opportunité.
- Une réponse OpenAI ne déclenche pas directement une publication.
- OpenAI ne doit pas inventer un prix, un stock, un délai ou des frais de
  livraison absents.
- Une observation concurrentielle sans source vérifiable ni date ne peut pas
  participer au calcul d'une opportunité.
- La décision commerciale finale reste humaine.

## Données externes

Les données fournisseurs et les résultats de recherche web suivent la
progression suivante :

```text
réponse externe
  -> validation du format
  -> normalisation
  -> rapprochement produit
  -> déduplication
  -> conservation limitée et datée
  -> analyse métier
```

Les identifiants externes doivent être utilisés pour mettre à jour les données
fournisseur existantes.

Une observation de prix comparable doit conserver au minimum :

- sa source ;
- son URL ;
- sa date d'observation ;
- son prix ;
- sa devise ;
- ses frais de livraison lorsqu'ils sont disponibles ;
- son niveau de similarité avec le produit étudié.

Une réponse sans source vérifiable ne constitue pas une observation de prix
exploitable.

Les réponses brutes, images et variantes ne doivent pas être conservées sans
justification.

Les limites de catégories, de produits fournisseurs, de candidats et de
résultats web sont des éléments de l'architecture, pas de simples options
d'interface.

## Références visuelles et recherche fournisseur

Chaque idée produit conserve des `supplier_search_keywords` et des `ProductIdeaVisualReference` associés à ces mots-clés. Les références visuelles sont recherchées indépendamment des fournisseurs ; elles servent de repères du type de produit recherché et non de modèle exact à reproduire.

Les recherches CJ, EPROLO, Printful et AW conservent sur chaque `SupplierOffer` le `supplier_search_keyword` qui a conduit à l'offre. Le contrôle visuel compare ensuite l'offre uniquement aux références liées à ce même mot-clé.

Le résultat Vision est persisté sur `SupplierOffer`. Lorsqu'une idée possède des références visuelles, une offre classée `rejected` ou dépourvue de résultat Vision ne poursuit pas vers la livraison, les prix comparables ou l'analyse financière. Ses anciens prix comparables courants sont archivés et restent disponibles comme historique.

Le fallback économique CJ vers le stock CN utilise exactement la même mécanique Vision que la collecte fournisseur principale. Il ne construit plus ses références à partir des images des `ComparablePrice`.

Les prix comparables restent une étape aval. Leur collecte recherche plusieurs domaines marchands distincts afin que la qualification repose sur des sources indépendantes.


## Livraison AW Dropship

AW Dropship ne fournit pas de devis de livraison temps réel avant la création de commande. EcommerceIA calcule donc le shipping en amont à partir du poids du SKU et de la grille tarifaire AW connue pour la France.

`AWShippingEstimator` utilise le poids total de la commande pour sélectionner la tranche tarifaire applicable. Le délai persistant est fixé de manière prudente à 6 jours ouvrés, correspondant à un jour maximum de préparation plus trois à cinq jours ouvrés de transport.

La méthode persistée reste générique sous le nom `AW Standard`. Le système ne déduit pas un transporteur précis à partir du poids seul tant qu'AW ne fournit pas une règle explicite de sélection.

Une offre AW sans poids exploitable reste incomplète et ne doit pas recevoir un coût de livraison inventé.


## Intelligence artificielle et calcul déterministe

L'intelligence artificielle convient notamment à :

- la formulation de catégories prometteuses ;
- la recherche et la synthèse de signaux publics ;
- la recherche web de produits et de prix comparables ;
- la classification ;
- le rapprochement sémantique ;
- l'explication ;
- l'identification de risques.

L'intelligence artificielle peut rechercher des informations récentes
uniquement lorsqu'un outil de recherche web est activé. Les faits commerciaux
retenus doivent rester associés à leurs sources et à leur date d'observation.

OpenAI recherche, rapproche, synthétise et explique. Il ne constitue pas la
source d'autorité pour les prix d'achat, les stocks, les délais ou les frais de
livraison.

Les opérations suivantes restent déterministes :

- conversion de devise ;
- calcul du coût livré ;
- prix concurrent médian ;
- dispersion des prix ;
- marge ;
- score de marge ;
- score de stock ;
- score de livraison ;
- score de confiance ;
- stock ;
- expiration ;
- règles d'autorisation ;
- changement de statut ;
- idempotence du paiement.

Une donnée inconnue reste inconnue. Elle ne doit jamais être remplacée
silencieusement par zéro.

Une sortie de modèle doit être validée avant d'entrer dans le domaine. Lorsque
le système attend des champs précis, la réponse doit respecter un schéma
structuré.

## Limites du parcours de découverte

Le parcours respecte les limites suivantes :

- cinq catégories maximum par génération ;
- cinq produits maximum par catégorie et par fournisseur ;
- préqualification des produits avant la recherche concurrentielle ;
- dix candidats maximum soumis à une recherche approfondie ;
- cinq observations de prix maximum par candidat.

Ces limites permettent de maîtriser les volumes, les coûts et le nombre
d'appels externes.

## Traçabilité

Une décision commerciale doit être reconstructible à partir des données
conservées :

- catégorie et besoin client ;
- produit et offre fournisseur ;
- sources et dates des prix comparables ;
- données manquantes ;
- calculs et scores ;
- recommandation ;
- validation humaine ;
- action exécutée.

Il n'est pas nécessaire de conserver chaque octet reçu d'une API ou d'une
recherche web. Il est nécessaire de conserver ce qui justifie la décision.

## Principes d'évolution

1. Une responsabilité par composant.
2. Réutiliser avant de créer.
3. Dépendre d'un contrat métier plutôt que d'un fournisseur particulier.
4. Construire d'abord le parcours manuel, puis assisté, puis automatisé.
5. Tester les règles responsables du comportement.
6. Mesurer avant d'augmenter les volumes.
7. Introduire des opérations asynchrones seulement lorsqu'elles deviennent
   nécessaires.
8. Conserver une source et une date pour chaque fait commercial utilisé.
9. Ne jamais transformer une donnée inconnue en donnée certaine.
10. Documenter toute décision qui modifie les frontières du système.

## Commandes fournisseurs

La commande client reste indépendante du fournisseur. Après paiement et
préparation financière, ses articles sont regroupés par fournisseur dans des
`SupplierOrder`. Chaque groupe est transmis par un adaptateur respectant le
même contrat : construire un payload, le valider et le soumettre.

`SupplierOrderAdapterFactory` sélectionne actuellement l'adaptateur CJ. Les
autres fournisseurs sont refusés tant que leur adaptateur n'est pas disponible.
La commande de gestion publique est `submit_supplier_order`; elle ne contient
aucune règle CJ spécifique.

En sandbox CJ, trois protections sont cumulées : option `--sandbox` obligatoire,
adaptateur réel désactivé et vérification de `isSandbox=1` jusque dans le client
HTTP. Le nom du transport choisi est persisté sur `SupplierOffer`. Les clés
d'idempotence, requêtes, réponses et identifiants externes sont conservés dans
le dossier fournisseur.

La simulation suit le cycle réellement exposé par CJ : création, confirmation,
paiement simulé, préparation, expédition puis livraison. Le statut CJ reste
stocké dans `SupplierOrder`, tandis qu'un service de synchronisation traduit
les états utiles vers le statut métier de `Order`.

Le transporteur et le suivi sont des données persistantes. Une réponse
incomplète ne remplace pas une valeur connue par une chaîne vide. Les suivis
sandbox sont marqués comme fictifs et ne génèrent aucun lien externe actif dans
l'espace client.

Le même contrat doit accueillir BigBuy, Printful ou un autre fournisseur. Un
fournisseur sans adaptateur explicite est refusé : aucune branche implicite ne
doit envoyer une commande en utilisant le protocole CJ.

## Estimation douanière

`CustomsDutyService` applique une règle datée selon l'origine, la destination,
la valeur intrinsèque, la quantité et la date. La première règle couvre le
droit européen temporaire de 3 EUR par article applicable aux petits envois
admissibles du 1er juillet 2026 au 30 juin 2028.

La préparation distingue la TVA, les droits estimés, le statut IOSS non vérifié
et les frais de dossier du transporteur. Ces derniers restent inconnus et non
inclus tant qu'aucune donnée fiable n'est disponible.

## Protection contre la vente à perte

`SupplierOfferAnalysisPipeline` calcule la rentabilité après conversion,
livraison et estimation douanière. Il ne crée aucune opportunité si le bénéfice
connu est nul ou négatif, ou si la marge nette est inférieure au seuil de
sécurité configuré. `OpportunityPublisher` répète le contrôle de perte juste
avant la publication afin d'empêcher un contournement du parcours normal.

Le contrôle ne transforme pas un coût inconnu en zéro certain. L'IOSS et les
frais de dossier inconnus restent visibles et devront devenir vérifiés avant
l'activation future des commandes fournisseurs réelles.

## Livraison gratuite CJ

CJ normalise le champ fournisseur `addMarkStatus` dans `SupplierOffer.free_shipping` : `1` signifie livraison explicitement gratuite, `0` signifie explicitement non gratuite et l'absence du champ reste inconnue (`None`).

`free_shipping=True` ne suffit pas à établir un coût de livraison de `0 USD` pour une destination donnée. La disponibilité logistique doit également être confirmée pour cette destination. En particulier, `postageAmount=0` avec `logisticsMiss=True` signifie qu'aucune méthode logistique exploitable n'est attachée à la commande et ne constitue pas une preuve de livraison gratuite.

Le délai de livraison reste indépendant du coût. Lorsque le coût, la route ou `free_shipping` ne permettent pas de conclure de manière fiable, EcommerceIA conserve l'information comme inconnue plutôt que de fabriquer une valeur de zéro.

Cette règle correspond à la décision D017 de `DECISIONS.md`.

## Origine des offres CJ

Depuis la décision D018 du 22 septembre 2026, la recherche fournisseur CJ du pipeline actif interroge directement la Chine (`CN`). L'ancienne stratégie de recherche Europe suivie d'un fallback vers CN est retirée du flux actif. `CJCountryFallbackService` peut rester dans le code comme historique, mais n'est plus branché au pipeline.

Les marchés cibles restent la France (`FR`), la Belgique (`BE`) et l'Espagne (`ES`). La recherche fournisseur détermine l'origine CN ; la prise en compte de chaque pays de destination appartient aux étapes aval de livraison et de coût rendu.

Le prochain chantier CJ doit établir le Landed Cost `CN -> FR/BE/ES` en distinguant le prix produit, le transport, les droits éventuels, la TVA/IOSS et les frais IOSS. Le chantier commande et facturation CJ vient ensuite.

Cette architecture correspond à la décision D018 de `DECISIONS.md`.
