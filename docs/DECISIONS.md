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

**Statut :** Acceptée

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
