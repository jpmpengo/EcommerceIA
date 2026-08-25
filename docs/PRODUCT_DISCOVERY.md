# Stratégie de découverte et de validation des produits

## Objectif

Ce document définit comment EcommerceIA découvre, documente et qualifie des
opportunités de produits sans aspirer de catalogues complets et sans dépendre
d'une intégration directe à une marketplace.

Le parcours combine :

- une recherche web sourcée assistée par OpenAI ;
- des données obtenues directement auprès des fournisseurs ;
- des calculs déterministes réalisés par EcommerceIA ;
- une décision finale conservée par le commerçant avec l'aide d'Emma.

## Problème

Les catalogues externes contiennent potentiellement des millions de produits.
Une collecte large entraînerait :

- trop d'appels externes ;
- beaucoup de doublons ;
- des traitements longs ;
- un stockage inutile ;
- des coûts difficiles à maîtriser ;
- des décisions impossibles à expliquer ;
- un risque de dépassement des quotas.

L'accès développeur aux grandes marketplaces est également difficile, instable
ou conditionné à l'acceptation d'un compte vendeur ou partenaire.

Une marketplace spécialisée peut en outre être inadaptée à une catégorie de
produits. Une absence de résultats ne signifie alors pas nécessairement que
l'idée est mauvaise.

La question n'est donc pas « comment importer les marketplaces ? », mais
« quelles catégories semblent prometteuses, quels produits les fournisseurs
peuvent-ils proposer et quelles données permettent de les évaluer ? ».

## Décision centrale

> Le système ne collecte pas des catalogues pour découvrir ensuite ce qui
> pourrait être utile. Il formule d'abord des hypothèses limitées, recherche
> des produits fournisseurs correspondants, puis collecte uniquement les
> données nécessaires pour évaluer les meilleurs candidats.

Le parcours de découverte ne dépend plus d'une connexion directe à Etsy,
Amazon, eBay, Cdiscount ou à une autre marketplace.

Une page provenant d'une marketplace peut apparaître dans les résultats d'une
recherche web. Elle est alors traitée comme une source publique datée, sans
utilisation de l'API de la marketplace.

## Responsabilités

### OpenAI recherche et propose

OpenAI peut :

- rechercher des signaux publics récents lorsque la recherche web est activée ;
- proposer exactement cinq catégories prometteuses ;
- regrouper plusieurs formulations d'un même besoin ;
- rapprocher une catégorie et des produits fournisseurs ;
- rechercher des produits et prix comparables ;
- fournir une justification, des sources, des risques et un niveau de
  confiance ;
- produire une réponse conforme à un schéma structuré ;
- expliquer les résultats calculés par EcommerceIA.

OpenAI ne doit pas :

- inventer des volumes de ventes ;
- présenter une catégorie comme une meilleure vente certaine sans preuve ;
- inventer un prix, un stock, un délai ou des frais de livraison ;
- affirmer une rentabilité sans données suffisantes ;
- remplacer une donnée inconnue par zéro ;
- publier un produit ;
- décider à la place du commerçant.

### Les fournisseurs décrivent la faisabilité

Les fournisseurs permettent de vérifier :

- le prix d'achat ;
- la devise ;
- le stock et la disponibilité ;
- les caractéristiques et variantes ;
- les dimensions ou capacités ;
- le pays d'expédition ;
- les frais et délais de livraison ;
- la compatibilité avec le pays de destination.

La présence d'un produit chez un fournisseur ne suffit pas à justifier sa
publication.

### EcommerceIA calcule

EcommerceIA normalise les données et calcule notamment :

- le prix concurrent médian ;
- la dispersion des prix ;
- le coût livré estimé ;
- la marge brute et la marge estimée ;
- le score de stock ;
- le score de livraison ;
- le score de similarité ;
- le score de complétude et de confiance ;
- le score global de l'opportunité.

Ces calculs sont déterministes, testés et reproductibles. OpenAI peut les
expliquer, mais ne constitue pas le moteur de calcul de référence.

### Emma pilote la décision

Emma :

- présente les catégories proposées et leurs sources ;
- explique les produits fournisseurs présélectionnés ;
- présente les prix comparables, les scores et les données manquantes ;
- permet au commerçant de retenir, reporter ou écarter une opportunité.

La décision finale reste humaine. Aucune publication n'est automatique.

## Concepts métier

### Signal public

Information sourcée et datée pouvant indiquer un besoin ou un intérêt : article
récent, tendance publique, comparaison de produits, recherche interne sans
résultat, demande saisonnière ou produit complémentaire.

### Catégorie prometteuse

Hypothèse commerciale formulée à partir de plusieurs signaux. Une catégorie
prometteuse n'est ni une meilleure vente certaine ni une opportunité validée.

### Produit fournisseur

Produit proposé par un fournisseur et susceptible de répondre au besoin associé
à une catégorie prometteuse.

### Offre fournisseur

Proposition d'approvisionnement associant un produit fournisseur à un prix
d'achat, une devise, un stock, une disponibilité et des informations de
livraison.

### Observation de prix comparable

Observation publique, datée et sourcée d'un produit suffisamment similaire au
produit fournisseur étudié.

Elle conserve au minimum :

- le nom du produit comparable ;
- le prix et la devise ;
- les frais de livraison lorsqu'ils sont disponibles ;
- le vendeur ou le site source ;
- l'URL ;
- la date d'observation ;
- le niveau de similarité avec le produit fournisseur.

Une réponse sans URL vérifiable ne constitue pas une observation de prix
exploitable.

### Opportunité

Produit fournisseur confronté à des observations de prix et à des données de
faisabilité suffisamment fiables pour permettre une décision commerciale.

## Flux retenu

```text
Contexte de la boutique
  -> recherche web assistée par OpenAI
  -> cinq catégories prometteuses sourcées
  -> recherche limitée auprès des fournisseurs
  -> produits et offres fournisseur
  -> préqualification fournisseur
  -> dix meilleurs candidats au maximum
  -> recherche web de prix comparables
  -> calcul déterministe des indicateurs et scores
  -> recommandation expliquée par Emma
  -> décision humaine
```

## Étape 1 — Découvrir cinq catégories prometteuses

OpenAI recherche et propose exactement cinq catégories adaptées aux pays et à
la clientèle ciblés.

Chaque proposition contient :

- le nom de la catégorie ;
- le besoin client ;
- le client cible ;
- les pays concernés ;
- les signaux commerciaux observés ;
- les sources et leur date ;
- les risques ;
- un niveau de confiance ;
- des termes de recherche fournisseur.

Une proposition sans source peut être conservée comme hypothèse, mais ne doit
pas être présentée comme une catégorie commercialement confirmée.

## Étape 2 — Rechercher les produits fournisseurs

Pour chaque catégorie, EcommerceIA interroge les fournisseurs configurés et
récupère au maximum cinq produits correspondants par fournisseur.

Le rapprochement prend notamment en compte :

- la fonction du produit ;
- le besoin client ;
- les caractéristiques principales ;
- les dimensions ou capacités ;
- les variantes ;
- les termes exclus.

Les produits sans prix d'achat exploitable ou indisponibles peuvent être
écartés avant la recherche concurrentielle.

## Étape 3 — Préqualifier les candidats

EcommerceIA effectue un premier classement avec les seules données fournisseur :

- prix d'achat ;
- stock ;
- disponibilité ;
- frais de livraison ;
- délai de livraison ;
- pays d'expédition ;
- complétude des données ;
- qualité du rapprochement avec la catégorie.

Dix candidats au maximum sont retenus pour la recherche approfondie. Cette
étape évite de payer des recherches web pour des produits déjà inexploitables.

## Étape 4 — Rechercher cinq prix comparables

Pour chaque candidat retenu, OpenAI utilise la recherche web afin de trouver
jusqu'à cinq offres réellement comparables.

Chaque résultat est validé avant son enregistrement. Les résultats trop éloignés,
anciens, incomplets ou dépourvus d'URL sont ignorés.

Une page de marketplace peut être utilisée comme source publique, mais aucune
connexion à son API développeur n'est nécessaire.

## Étape 5 — Calculer et présenter les opportunités

EcommerceIA calcule les indicateurs et le score global. Emma présente ensuite :

- le produit et son fournisseur ;
- les coûts et délais connus ;
- les prix comparables avec leurs sources ;
- la marge et les scores ;
- les données manquantes ;
- les risques ;
- une recommandation expliquée.

Le commerçant peut :

- retenir l'opportunité ;
- la reporter ;
- l'écarter.

## Contexte fourni à OpenAI

La génération doit être encadrée par :

- les pays et la clientèle visés ;
- les catégories autorisées ou interdites ;
- les produits déjà présents dans la boutique ;
- la fourchette de prix souhaitée ;
- les contraintes de poids, de fragilité et de livraison ;
- les produits réglementés ou interdits ;
- les signaux internes disponibles ;
- le nombre exact de catégories attendu ;
- l'obligation de citer les sources utilisées ;
- l'interdiction d'inventer des données commerciales.

## Structure minimale d'une catégorie

```json
{
  "name": "Accessoires ergonomiques pour poste de travail",
  "customer_need": "Améliorer le confort pendant le travail quotidien",
  "target_customer": "Télétravailleurs et utilisateurs de bureau",
  "countries": [
    "FR",
    "BE",
    "ES"
  ],
  "supplier_queries": [
    "ergonomic desk accessory",
    "accessoire bureau ergonomique"
  ],
  "excluded_terms": [
    "used",
    "replacement part",
    "broken"
  ],
  "signals": [
    "besoin mentionné dans plusieurs sources récentes"
  ],
  "risks": [
    "marché concurrentiel",
    "qualité ergonomique difficile à vérifier"
  ],
  "confidence": "medium",
  "sources": [
    {
      "title": "Titre de la source",
      "url": "https://example.com/source",
      "observed_at": "2026-08-25"
    }
  ]
}
```

## Structure minimale d'une observation de prix

```json
{
  "product_name": "Accessoire ergonomique comparable",
  "price": "39.90",
  "currency": "EUR",
  "shipping_cost": null,
  "seller": "Nom du vendeur ou du site",
  "product_url": "https://example.com/product",
  "observed_at": "2026-08-25",
  "similarity_score": 0.87
}
```

Une valeur `null` représente une donnée inconnue. Elle ne doit pas être
interprétée comme une valeur nulle ou gratuite.

## Garde-fous de la première version

Pour une campagne :

- lancement manuel par Emma ;
- cinq catégories proposées exactement ;
- cinq produits maximum par catégorie et par fournisseur ;
- dix candidats maximum après préqualification ;
- cinq observations de prix maximum par candidat ;
- nombre de fournisseurs configurés limité ;
- aucune collecte complète de catalogue ;
- aucune image téléchargée pendant la phase de découverte ;
- aucune publication automatique ;
- déduplication par fournisseur et identifiant externe ;
- déduplication des observations de prix par URL et date ;
- conservation explicite des données manquantes.

Ces valeurs constituent des plafonds initiaux. Toute augmentation doit être
précédée d'une mesure de durée, de coût, de quota et de croissance de la base.

## Traçabilité obligatoire

Le système doit conserver ce qui permet d'expliquer une décision :

- contexte et instructions envoyés à OpenAI ;
- date de génération ;
- catégories proposées ;
- sources publiques utilisées ;
- produits et offres fournisseur examinés ;
- raisons de la préqualification ;
- requêtes web exécutées ;
- prix comparables retenus et rejetés ;
- URLs et dates d'observation ;
- données manquantes ;
- calculs et scores ;
- recommandation présentée ;
- décision humaine.

Les réponses brutes non retenues doivent rester temporaires ou supprimables.

## Première version fonctionnelle

1. Emma lance manuellement une campagne de découverte.
2. OpenAI retourne exactement cinq catégories structurées et sourcées.
3. EcommerceIA interroge les fournisseurs configurés pour ces catégories.
4. Chaque fournisseur retourne au maximum cinq produits par catégorie.
5. EcommerceIA normalise, déduplique et préqualifie les produits.
6. Dix candidats maximum sont conservés.
7. OpenAI recherche jusqu'à cinq prix comparables par candidat.
8. EcommerceIA valide et enregistre les observations sourcées.
9. Les calculs déterministes évaluent la marge, le stock, la livraison, la
   similarité et la confiance.
10. Emma présente une recommandation expliquée.
11. Le commerçant retient, reporte ou écarte l'opportunité.

La planification automatique, Celery et les imports récurrents ne sont pas
nécessaires pour valider cette première version en local.

## Prototype OpenAI du 23 août 2026

Le premier prototype a confirmé qu'OpenAI pouvait produire cinq hypothèses
structurées :

- en nombre limité ;
- centrées sur un problème client ;
- adaptées aux pays demandés ;
- accompagnées de mots-clés exploitables ;
- dépourvues de chiffres de ventes inventés.

Ce prototype n'utilisait ni recherche web, ni données fournisseur, ni preuve de
prix. Il validait uniquement le format de génération.

Les cinq idées obtenues ne constituent donc pas des opportunités commerciales
validées. Elles restent des données historiques et pourront être réexaminées
avec le nouveau parcours.

## Hors périmètre immédiat

- intégration directe à une marketplace ;
- collecte massive de catalogues ;
- affirmation certaine des cinq meilleures ventes du marché ;
- publication automatique ;
- décision commerciale entièrement automatisée ;
- remplacement des données absentes par des estimations non signalées ;
- planification récurrente des campagnes.

## Documentation associée

Voir `DECISIONS.md`, `ARCHITECTURE.md`, `ROADMAP.md` et `EMMA.md`.
