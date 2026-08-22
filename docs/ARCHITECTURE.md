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
Signaux et sources externes
  -> idées produit
  -> observations de marché
  -> offres fournisseur
  -> qualification
  -> opportunités
  -> validation humaine
  -> catalogue
  -> commande client
  -> paiement
  -> approvisionnement
  -> expédition et suivi
```

Une opportunité, une offre fournisseur, un produit publié et une commande
client sont des objets distincts. Ils ne doivent jamais être confondus.

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

`product_intelligence` collecte et normalise les informations nécessaires à
l'étude des idées :

- clients d'API ;
- importateurs et moteurs de recherche ;
- observations de marché ;
- fournisseurs et offres fournisseur ;
- extraction des caractéristiques ;
- comparaison des produits ;
- conversion des devises ;
- estimation de la livraison ;
- qualification et création d'opportunités.

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
reste du domaine ne doit pas dépendre directement du format d'une API.

### Importers et Searchers

Ils transforment une source externe en données candidates, dans les limites
imposées par une recherche ciblée.

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

## Données externes

Les intégrations suivent la progression suivante :

```text
réponse externe
  -> validation du format
  -> normalisation
  -> déduplication
  -> conservation limitée
  -> analyse métier
```

Les identifiants externes doivent être utilisés pour mettre à jour les données
existantes. Les réponses brutes, images et variantes ne doivent pas être
conservées sans justification.

Les limites d'appels, de pages et de résultats sont des éléments de
l'architecture, pas de simples options d'interface.

## Intelligence artificielle et calcul déterministe

L'intelligence artificielle convient notamment à :

- la formulation d'idées ;
- la recherche et la synthèse de signaux publics ;
- la classification ;
- la similarité sémantique ;
- l'explication ;
- l'identification de risques.

Les opérations suivantes restent déterministes :

- conversion de devise ;
- calcul de coût ;
- marge ;
- stock ;
- expiration ;
- règles d'autorisation ;
- changement de statut ;
- idempotence du paiement.

Une sortie de modèle doit être validée avant d'entrer dans le domaine. Lorsque
le système attend des champs précis, la réponse doit respecter un schéma
structuré.

## Traçabilité

Une décision commerciale doit être reconstructible à partir des données
conservées : source, date, calculs, recommandation, validation humaine et action
exécutée.

Il n'est pas nécessaire de conserver chaque octet reçu d'une API. Il est
nécessaire de conserver ce qui justifie la décision.

## Principes d'évolution

1. Une responsabilité par composant.
2. Réutiliser avant de créer.
3. Dépendre d'un contrat métier plutôt que d'un fournisseur particulier.
4. Construire d'abord le parcours manuel, puis assisté, puis automatisé.
5. Tester les règles responsables du comportement.
6. Mesurer avant d'augmenter les volumes.
7. Introduire des opérations asynchrones seulement lorsqu'elles deviennent
   nécessaires.
8. Documenter toute décision qui modifie les frontières du système.
