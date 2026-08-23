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
- cinq idées proposées au maximum ;
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
2. OpenAI retourne au maximum cinq idées structurées.
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

## Premier prototype OpenAI validé

### Exécution

- Date : 23 août 2026
- Modèle : `gpt-5.6-luna`
- Interface : Responses API avec Structured Outputs
- Nombre demandé : 5 idées
- Nombre obtenu : 5 idées
- Marchés : France, Belgique et Espagne
- Enregistrement en base : non
- Recherche Web : non
- Recherche marketplace : non
- Recherche fournisseur : non

Ce premier appel avait pour objectif de vérifier qu’OpenAI pouvait produire une
courte liste d’hypothèses structurées et exploitables, sans importer de catalogue
et sans inventer de chiffres de ventes.

### Idée 1 — Organisateur modulaire pour coffre de voiture familiale

**Problème client**

Les courses, poussettes, équipements de sport et objets du quotidien se déplacent
dans le coffre et se renversent pendant les trajets. Le produit serait un système
pliable composé de compartiments réglables, de séparateurs amovibles, d’un fond
antidérapant et de sangles de fixation adaptées aux différents coffres.

**Client cible**

Familles, conducteurs utilisant régulièrement leur voiture pour les courses,
parents de jeunes enfants et personnes transportant plusieurs catégories
d’objets dans leur coffre.

**Pourquoi l’étudier**

Le besoin est concret, fréquent et lié à l’organisation de l’espace dans un
véhicule. L’idée mérite une étude des dimensions de coffres les plus courantes,
des attentes en matière de résistance et de nettoyage, ainsi que des différences
de compatibilité entre modèles de voitures dans les trois pays.

**Pays**

- France
- Belgique
- Espagne

**Mots-clés**

- organisateur coffre voiture pliable
- rangement coffre voiture familial
- séparateur coffre voiture
- coffre voiture poussette courses
- car trunk organizer adjustable

### Idée 2 — Kit de réduction des courants d’air pour portes et fenêtres anciennes

**Problème client**

Les logements équipés de portes ou fenêtres anciennes peuvent présenter des
passages d’air autour des ouvrants, avec une sensation d’inconfort et des
nuisances sonores potentielles. Le kit comprendrait plusieurs solutions
compatibles avec différents supports : joints adhésifs, boudin de bas de porte,
profilés de calfeutrage et outils de mesure simples.

**Client cible**

Locataires et propriétaires de logements anciens, occupants souhaitant améliorer
le confort intérieur sans travaux lourds et personnes recherchant des solutions
réversibles.

**Pourquoi l’étudier**

Le produit répond à un problème facilement observable et pourrait être proposé
sous forme de kit guidé par type de fenêtre ou de porte. Une étude devrait
vérifier la compatibilité avec les matériaux et formats présents en France, en
Belgique et en Espagne, ainsi que la clarté des instructions d’installation.

**Pays**

- France
- Belgique
- Espagne

**Mots-clés**

- kit calfeutrage fenêtre
- joint isolant fenêtre ancienne
- bas de porte anti courant d’air
- joint fenêtre bois PVC
- réduire courant d’air porte appartement

### Idée 3 — Station de séchage et de rangement pour accessoires de sport humide

**Problème client**

Les chaussures, gants, casques, protections et vêtements utilisés sous la pluie
ou après une activité sportive restent difficiles à faire sécher et peuvent
encombrer l’entrée. La station serait un support vertical ventilé, démontable,
avec bacs de récupération d’eau, crochets et emplacements distincts pour les
chaussures et petits accessoires.

**Client cible**

Familles pratiquant des sports de plein air, cyclistes, randonneurs, utilisateurs
de trottinettes ou de vélos et foyers disposant d’un espace d’entrée limité.

**Pourquoi l’étudier**

Cette idée combine rangement, séchage et protection des sols dans un seul
produit. Elle mérite une étude sur les usages selon les climats et activités
sportives, la stabilité du support, la facilité de nettoyage et la demande de
formats compacts pour les appartements.

**Pays**

- France
- Belgique
- Espagne

**Mots-clés**

- séchoir chaussures sport
- rangement équipement sportif humide
- support séchage chaussures vélo
- organisateur entrée chaussures mouillées
- station séchage casque gants chaussures

### Idée 4 — Boîte de conservation ventilée pour fruits et légumes fragiles

**Problème client**

Certains fruits et légumes s’abîment rapidement lorsqu’ils sont stockés ensemble
ou lorsque l’humidité s’accumule dans le réfrigérateur. Le produit serait une
boîte empilable avec ventilation réglable, séparateurs, bac récupérateur
d’humidité et repères indiquant les zones de rangement recommandées.

**Client cible**

Ménages souhaitant mieux organiser leur réfrigérateur, personnes vivant seules
ou en couple, consommateurs préparant leurs repas à l’avance et foyers cherchant
à limiter le gaspillage alimentaire.

**Pourquoi l’étudier**

Le concept associe organisation du réfrigérateur et conservation de produits
frais, avec des possibilités de déclinaison par taille et par catégorie
d’aliments. Une validation devrait porter sur les dimensions des réfrigérateurs,
les matériaux acceptés au contact alimentaire, le nettoyage et la compréhension
des réglages de ventilation.

**Pays**

- France
- Belgique
- Espagne

**Mots-clés**

- boîte conservation fruits légumes frigo
- rangement légumes réfrigérateur ventilé
- bac anti humidité fruits légumes
- organisateur frigo fruits légumes
- boîte conservation légumes empilable

### Idée 5 — Trousse de réparation textile compacte pour vêtements du quotidien

**Problème client**

Les petits accrocs, boutons décousus, ourlets défaits et fermetures endommagées
sont souvent difficiles à réparer rapidement avec une trousse standard peu
organisée. Le produit regrouperait des aiguilles adaptées à différents tissus,
des fils assortis, des mini-ciseaux, un mètre souple, des épingles de sûreté, un
crochet de reprise et un guide illustré multilingue.

**Client cible**

Adultes souhaitant prolonger la durée de vie de leurs vêtements, étudiants,
voyageurs, parents et personnes recherchant une solution compacte pour les
réparations courantes.

**Pourquoi l’étudier**

Le format peut répondre à plusieurs contextes d’usage : domicile, voyage, bureau
ou résidence étudiante. L’étude devrait comparer les besoins des débutants et
des utilisateurs expérimentés, identifier les réparations les plus recherchées
et vérifier la pertinence d’un assortiment de couleurs et d’outils pour les
marchés ciblés.

**Pays**

- France
- Belgique
- Espagne

**Mots-clés**

- kit réparation vêtements couture
- trousse couture débutant compacte
- kit réparer bouton fermeture éclair
- trousse couture voyage
- kit reprise accroc vêtement

### Conclusion du prototype

Le prototype est concluant.

OpenAI a produit cinq hypothèses :

- limitées en nombre ;
- homogènes ;
- centrées sur un problème client ;
- adaptées aux marchés demandés ;
- accompagnées de mots-clés exploitables ;
- dépourvues de chiffres de ventes inventés.

Ces idées ne constituent pas des opportunités commerciales validées et ne
doivent pas être publiées directement.

L’organisateur modulaire pour coffre de voiture familiale est retenu comme
premier candidat à une future validation marketplace ciblée. Cette sélection
reste une décision humaine et ne constitue pas encore une approbation
commerciale.
