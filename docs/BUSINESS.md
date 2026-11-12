# Modèle métier d'EcommerceIA

## Objectif

Ce document décrit les règles commerciales durables et les principaux cycles
de vie du projet.

## Parcours de l'internaute

Le parcours de vente doit rester court :

1. découverte du catalogue ;
2. consultation d'un produit ;
3. ajout au panier ;
4. saisie des coordonnées ;
5. création de la commande ;
6. paiement ;
7. suivi de la commande.

La consultation du catalogue, le panier et la commande ne nécessitent pas de
compte. Une commande invitée reste accessible depuis le navigateur qui l'a
créée. Elle peut également être récupérée au moyen d'un code temporaire envoyé
à l'adresse utilisée lors de la commande.

Après l'achat, l'internaute peut créer un compte. Les commandes invitées de la
session ayant la même adresse e-mail sont alors rattachées à ce compte.

## Commande, réservation et paiement

- Une commande en attente réserve le stock pendant une durée limitée.
- Le stock physique n'est diminué qu'après confirmation du paiement.
- Une réservation expirée ne bloque plus le stock disponible.
- La confirmation du paiement doit être idempotente : un même événement ne
  diminue jamais le stock deux fois.
- Une commande payée ne peut plus être annulée comme une commande en attente.
- Le paiement doit rester accessible au propriétaire du compte ou à la session
  invitée autorisée.

## Cycle de vie d'une idée commerciale

```text
Signal
  -> idée produit
  -> étude du marché
  -> recherche fournisseur
  -> opportunité qualifiée
  -> décision d'Emma
  -> produit publié
```

Une idée est une hypothèse. Une observation de marché est un élément de preuve.
Une offre fournisseur établit la faisabilité. Une opportunité rassemble les
éléments nécessaires à une décision.

La stratégie détaillée est définie dans `PRODUCT_DISCOVERY.md`.

## Cycle de vie d'une opportunité

### Détection et analyse

Une opportunité détectée est analysée selon les données disponibles :

- prix de marché ;
- coût d'achat ;
- marge estimée ;
- concurrence ;
- stock fournisseur ;
- livraison ;
- caractéristiques comparables ;
- risques et niveau de confiance.

### Approbation

Le commerçant peut approuver une opportunité lorsqu'elle mérite une décision
de publication.

### Réanalyse après approbation

Une opportunité en `review` devenue `unprofitable` ou `incomplete` est écartée de la décision courante. Une opportunité déjà `approved` qui devient `unprofitable` ou `incomplete` revient en `review` : les conditions ayant changé, le commerçant doit l'approuver de nouveau avant toute publication. Une opportunité encore en `review` et toujours viable peut voir ses données financières actualisées ; une opportunité déjà `approved` et toujours viable n'est pas réécrite silencieusement par la réanalyse.

### Décisions possibles

#### Publier

La publication crée un produit vendable et relie ce produit à son opportunité.

#### Reporter

Une opportunité approuvée peut être reportée pendant 14 jours :

- aucun produit n'est créé ;
- l'opportunité reste conservée ;
- elle est masquée des recommandations prioritaires ;
- elle redevient éligible après la date de report.

#### Rejeter

Une opportunité rejetée est conservée dans l'historique et ne réapparaît pas.
Une nouvelle opportunité concernant une famille de produits similaire peut
toutefois être créée si les conditions du marché ont changé de manière
significative.

## Règles de publication

Une opportunité ne peut être publiée que si :

- elle a été approuvée ;
- une catégorie est définie ;
- une description est renseignée ;
- un stock initial est supérieur à zéro ;
- une offre fournisseur acceptable a été validée ;
- elle n'a pas déjà été publiée.

Une publication ne doit jamais être effectuée uniquement pour remplir le
catalogue.

## Priorisation

- Le Dashboard présente un petit nombre d'actions prioritaires.
- Emma propose une seule priorité principale lorsqu'une action utile existe.
- Une priorité conduit toujours à une action et en explique le bénéfice.
- Lorsqu'aucune action n'est utile, Emma le dit explicitement.
- Un score doit être accompagné de ses raisons et de ses limites.

## Approvisionnement cible

Le processus cible après paiement est :

```text
Commande payée
  -> préparation de la commande fournisseur
  -> commande fournisseur
  -> expédition
  -> suivi
  -> livraison
```

Cette automatisation sera construite progressivement : d'abord manuelle, puis
assistée, et seulement ensuite automatisée si les étapes précédentes sont
fiables.
