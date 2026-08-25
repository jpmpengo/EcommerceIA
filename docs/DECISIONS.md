# Décisions d'architecture et de produit

Ce document conserve uniquement les décisions durables. Les descriptions
détaillées appartiennent aux documents spécialisés.

## D001 — Séparer les calculs avec OpportunityAnalyzer

**Statut :** Acceptée

### Contexte

Les calculs d'opportunité ne doivent pas être dispersés dans les modèles, les
vues ou les templates.

### Décision

`OpportunityAnalyzer` porte les calculs nécessaires à l'analyse d'une
opportunité.

### Conséquences

Les règles de calcul sont testables et réutilisables. Les autres composants ne
doivent pas les réimplémenter.

## D002 — Séparer la publication avec OpportunityPublisher

**Statut :** Acceptée

### Contexte

La publication contient des règles métier et ne doit pas dépendre de Django
Admin ou d'une vue particulière.

### Décision

`OpportunityPublisher` transforme une opportunité validée en produit.

### Conséquences

L'interface demande la publication, mais le service en protège les règles.

## D003 — Faire du Dashboard l'interface métier

**Statut :** Acceptée

### Contexte

Le commerçant ne doit pas travailler quotidiennement dans Django Admin.

### Décision

Le Dashboard devient la porte d'entrée de l'espace commerçant. Django Admin
reste réservé aux opérations techniques.

### Conséquences

Les actions, explications et priorités sont conçues pour le commerçant.

## D004 — Isoler les fournisseurs derrière des contrats

**Statut :** Remplacée par D009

### Contexte

Les sources peuvent être remplacées ou complétées : API, fichiers ou nouveaux
fournisseurs.

### Décision

Les clients, Providers, Importers et Searchers isolent les formats externes du
domaine métier.

### Conséquences

Une intégration peut évoluer sans réécrire le pipeline complet.

## D005 — Préparer le briefing hors des vues

**Statut :** Acceptée

### Contexte

Une vue ne doit pas décider seule de ce qu'Emma dit au commerçant.

### Décision

Un service de briefing prépare les informations et messages nécessaires à la
journée du commerçant.

### Conséquences

Le discours d'Emma devient testable, cohérent et indépendant de l'affichage.

## D006 — Expliquer les recommandations avec OpportunityAdvisor

**Statut :** Acceptée

### Contexte

Un score et une marge ne suffisent pas à établir la confiance.

### Décision

`OpportunityAdvisor` transforme les indicateurs en recommandation
compréhensible.

### Conséquences

EcommerceIA explique ses conclusions et distingue les raisons des actions
exécutées.

## D007 — Créer un Advisor pour une interprétation complexe

**Statut :** Acceptée

### Contexte

Certains domaines nécessitent une interprétation spécialisée, mais tous les
services ne doivent pas devenir des Advisors.

### Décision

Un Advisor est créé lorsqu'un domaine devient suffisamment complexe pour
justifier un spécialiste de l'analyse et de l'explication.

### Conséquences

Un Advisor conseille sans exécuter. Les calculs déterministes restent dans les
services responsables.

## D008 — Découvrir les produits avant de collecter les catalogues

**Date :** 22 août 2026

**Statut :** Acceptée

### Contexte

Les marketplaces et fournisseurs possèdent des catalogues trop importants pour
être parcourus ou importés sans ciblage préalable. Une collecte large créerait
des volumes, coûts, doublons et traitements disproportionnés.

### Décision

Utiliser OpenAI pour proposer une courte liste d'idées sourcées dans un cadre
commercial défini. Emma permet au commerçant de sélectionner les idées à
étudier. Les marketplaces et fournisseurs sont ensuite interrogés avec des
limites explicites uniquement pour ces idées.

### Raisons

- maîtriser les volumes et les coûts ;
- limiter les appels API ;
- éviter les imports inutiles ;
- conserver une décision humaine ;
- rendre chaque opportunité explicable ;
- séparer l'hypothèse des preuves commerciales.

### Conséquences

- OpenAI propose mais ne prouve ni ventes ni rentabilité ;
- Emma sélectionne les idées ;
- les recherches marketplace sont plafonnées ;
- les fournisseurs interviennent après validation du marché ;
- aucune publication n'est automatique ;
- les données justifiant la décision sont traçables.

### Documentation associée

Voir `PRODUCT_DISCOVERY.md`.

## D009 — Remplacer les intégrations marketplaces par une recherche web sourcée

**Date :** 25 août 2026

**Statut :** Acceptée

### Contexte

L’accès développeur aux grandes marketplaces est difficile, instable ou soumis
à l’acceptation d’un compte vendeur ou partenaire.

Une marketplace spécialisée ne convient pas nécessairement à toutes les
catégories de produits. Une absence de résultats peut alors provenir d’une
source inadaptée et non d’un manque d’intérêt commercial pour le produit.

Les intégrations directes aux marketplaces compliquent donc le projet sans
garantir une validation fiable de toutes les idées.

### Décision

Abandonner les intégrations directes aux marketplaces dans le parcours de
découverte des opportunités.

Le nouveau parcours est le suivant :

1. OpenAI recherche et propose cinq catégories prometteuses documentées ;
2. les fournisseurs configurés proposent jusqu’à cinq produits correspondant
   à chaque catégorie ;
3. les produits sont préclassés selon les données disponibles auprès des
   fournisseurs ;
4. OpenAI effectue une recherche web sourcée pour trouver jusqu’à cinq prix
   comparables pour chaque produit retenu ;
5. EcommerceIA calcule les marges et les différents scores ;
6. Emma présente les opportunités au commerçant pour décision finale.

### Responsabilités

- OpenAI recherche, rapproche, synthétise et explique ;
- les fournisseurs fournissent les prix d’achat, stocks, variantes, délais et
  frais de livraison ;
- EcommerceIA normalise les données et effectue les calculs déterministes ;
- Emma présente les résultats et accompagne la décision ;
- le commerçant conserve la décision finale.

OpenAI ne constitue pas, à lui seul, une preuve de vente, de prix, de stock ou
de rentabilité. Toute information commerciale actuelle doit être associée à
une source vérifiable et à une date d’observation.

### Limites

- cinq catégories maximum par génération ;
- cinq produits maximum par catégorie et par fournisseur ;
- dix candidats maximum soumis à une recherche concurrentielle approfondie ;
- cinq observations de prix maximum par candidat ;
- aucune donnée manquante ne doit être remplacée silencieusement par zéro ;
- aucune publication de produit ne doit être automatique.

### Conséquences

- EcommerceIA ne dépend plus d’une API Etsy, Amazon, eBay, Cdiscount ou d’une
  autre marketplace pour découvrir des opportunités ;
- une page de marketplace peut apparaître comme source dans une recherche web
  sans nécessiter une intégration à son API ;
- les anciens modèles et services liés aux marketplaces seront remplacés
  progressivement ;
- les données historiques utiles seront conservées ou migrées avant toute
  suppression ;
- les scores de marge, stock, livraison et risque restent calculés par du code
  Python testé et reproductible ;
- la recherche web et les données fournisseurs restent traçables ;
- la décision finale reste humaine.

### Documentation associée

Voir `ARCHITECTURE.md`, `PRODUCT_DISCOVERY.md`, `ROADMAP.md` et `EMMA.md`.
