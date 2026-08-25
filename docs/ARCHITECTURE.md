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