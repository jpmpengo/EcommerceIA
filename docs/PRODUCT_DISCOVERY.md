# Stratégie de découverte et de validation des produits

## Objectif

Ce document définit comment EcommerceIA obtient des idées de produits sans
aspirer les catalogues complets des marketplaces ou des fournisseurs.

## Problème

Les marketplaces contiennent potentiellement des millions d'annonces. Une
collecte large entraînerait :

- trop d'appels API ;
- beaucoup de doublons ;
- des traitements longs ;
- un stockage inutile ;
- des coûts difficiles à maîtriser ;
- des décisions impossibles à expliquer ;
- un risque de dépassement des quotas.

La question n'est donc pas « comment importer les marketplaces ? », mais
« quelles idées méritent une étude et pourquoi ? ».

## Décision centrale

> Le système ne collecte pas des catalogues pour découvrir ensuite ce qui
> pourrait être utile. Il formule d'abord une hypothèse limitée, puis collecte
> uniquement les données nécessaires pour la vérifier.

L'API OpenAI peut rechercher sur le Web et proposer une courte liste d'idées
sourcées. Ces idées restent des hypothèses. Les marketplaces mesurent le
marché, les fournisseurs déterminent la faisabilité et Emma laisse la décision
finale au commerçant.

## Responsabilités

### OpenAI propose

OpenAI peut :

- rechercher des signaux publics récents ;
- repérer des produits fréquemment cités ;
- regrouper plusieurs formulations d'une même idée ;
- proposer des produits cohérents avec la boutique ;
- fournir une justification, des sources, des risques et des mots-clés ;
- produire une réponse conforme à un schéma structuré.

OpenAI ne doit pas :

- inventer des volumes de ventes ;
- affirmer une rentabilité sans données ;
- publier un produit ;
- déclencher seul une collecte massive ;
- décider à la place du commerçant.

### Les marketplaces valident le marché

Une marketplace répond à des questions ciblées :

- le produit est-il proposé ?
- dans quelle fourchette de prix ?
- quelles variantes sont courantes ?
- combien d'offres comparables apparaissent dans l'échantillon ?
- quels signaux publics de concurrence ou de demande sont disponibles ?

Elle n'est jamais considérée comme un catalogue à recopier.

### Les fournisseurs valident la faisabilité

Les fournisseurs permettent de vérifier :

- le prix d'achat ;
- la devise ;
- le stock ;
- les caractéristiques et variantes ;
- les dimensions ou capacités ;
- les frais et délais de livraison ;
- la compatibilité avec le pays de destination ;
- la marge potentielle.

La présence d'un produit chez un fournisseur ne suffit pas à justifier sa
publication.

### Emma pilote

Emma présente les idées, leurs raisons, leurs sources et leurs risques. Elle
permet au commerçant de sélectionner les idées à étudier, de déclencher les
recherches limitées et d'accepter, reporter ou rejeter une opportunité.

## Concepts métier

### Signal

Information pouvant indiquer un besoin : tendance publique, recherche interne
sans résultat, produit fréquemment consulté, demande saisonnière ou produit
complémentaire.

### Idée produit

Hypothèse formulée à partir d'un ou plusieurs signaux. Une idée n'est pas une
opportunité et ne doit pas être publiée.

### Observation de marché

Échantillon daté et sourcé permettant d'évaluer le prix, la concurrence, les
variantes et la confiance associée à l'étude.

### Offre fournisseur

Proposition d'approvisionnement associant un produit comparable à un coût, un
stock, une livraison et des caractéristiques.

### Opportunité

Idée confrontée à des données de marché et à une offre fournisseur suffisamment
fiables pour permettre une décision commerciale.

## Flux retenu

```text
Contexte de la boutique
  -> recherche web assistée par OpenAI
  -> idées sourcées
  -> sélection par Emma
  -> recherche marketplace limitée
  -> recherche fournisseur limitée
  -> calcul déterministe
  -> recommandation expliquée
  -> décision humaine
```

## Contexte fourni à OpenAI

La génération doit être encadrée par :

- le pays et la clientèle visés ;
- les catégories autorisées ;
- les produits déjà présents ;
- la fourchette de prix souhaitée ;
- les contraintes de poids, fragilité et livraison ;
- les produits réglementés ou interdits ;
- les signaux internes disponibles ;
- le nombre maximal d'idées attendu.

## Structure minimale d'une idée

```json
{
  "name": "Souris verticale silencieuse",
  "category": "Informatique",
  "customer_need": "Réduire l'inconfort pendant le travail",
  "reason": "Produit complémentaire aux accessoires de bureau",
  "target_price_min": 25,
  "target_price_max": 60,
  "marketplace_queries": [
    "souris verticale silencieuse",
    "silent ergonomic vertical mouse"
  ],
  "excluded_terms": [
    "replacement part",
    "broken",
    "used"
  ],
  "signals": [
    "présence dans plusieurs sources récentes"
  ],
  "risks": [
    "marché concurrentiel",
    "qualité ergonomique difficile à vérifier"
  ],
  "confidence": "medium",
  "sources": []
}
```

## Garde-fous de la première version locale

Pour une campagne :

- lancement manuel par Emma ;
- dix idées proposées au maximum ;
- trois idées sélectionnées au maximum ;
- deux marketplaces au maximum par idée ;
- deux pages au maximum par marketplace ;
- vingt résultats utiles au maximum par recherche ;
- nombre d'offres fournisseur plafonné ;
- aucune image téléchargée pendant la phase d'idée ;
- aucune publication automatique ;
- déduplication par source et identifiant externe.

Ces valeurs constituent des plafonds initiaux. Toute augmentation doit être
précédée d'une mesure de durée, de coût, de quota et de croissance de la base.

## Traçabilité obligatoire

Le système doit conserver ce qui permet d'expliquer une décision :

- origine de l'idée ;
- contexte et instructions envoyés ;
- date de génération ;
- sources publiques utilisées ;
- sélection ou rejet par Emma ;
- requêtes marketplace exécutées ;
- nombre de résultats examinés ;
- offres fournisseur comparées ;
- calculs et raisons de la décision.

Les réponses brutes non retenues doivent rester temporaires ou supprimables.

## Première version fonctionnelle

1. Emma lance une génération manuelle.
2. OpenAI retourne au maximum dix idées structurées et sourcées.
3. Le commerçant en sélectionne au maximum trois.
4. Le système prépare les requêtes marketplace.
5. Emma déclenche la recherche.
6. Les résultats sont plafonnés, normalisés et dédupliqués.
7. Les fournisseurs sont interrogés seulement pour les idées retenues.
8. Les calculs déterministes évaluent la faisabilité.
9. Emma présente une recommandation expliquée.
10. Le commerçant décide.

La planification automatique, Celery et les imports récurrents ne sont pas
nécessaires pour valider cette première version en local.
