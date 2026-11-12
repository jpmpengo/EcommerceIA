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

## D010 — Conserver une décision humaine aux deux portes du parcours

**Date :** 27 août 2026

**Statut :** Acceptée

### Décision

Le parcours de découverte comporte deux autorisations humaines distinctes :

1. une idée `proposed` passe à `selected` lorsque le commerçant autorise son
   étude ;
2. une opportunité `review` passe à `approved` lorsque le commerçant autorise
   sa préparation.

La publication reste une troisième action explicite. Emma peut proposer,
expliquer et préparer les actions, mais ne franchit aucune de ces portes sans
le commerçant.

Le stock initial publié est plafonné par la règle
`min(stock fournisseur, 10)`. Une absence de stock fournisseur ne doit jamais
être transformée silencieusement en stock disponible.

Le compte opérateur dispose d'un aperçu de la boutique, mais ne doit pas suivre
le parcours d'achat dans la même session qu'un client.

### Conséquences

- le PILOTAGE est l'interface humaine du parcours ;
- les commandes de gestion restent des outils d'exécution et de diagnostic ;
- le futur orchestrateur nocturne prépare les résultats sans publier ;
- les essais de commande utilisent une session client séparée ;
- chaque transition reste traçable et réversible jusqu'à la publication.

Le compte rendu détaillé du premier test est conservé dans
`E2E_IDEA_16_20260827.md`.

## D011 — Commander par adaptateurs fournisseurs et tester CJ en sandbox

**Date :** 27 août 2026

**Statut :** Acceptée

### Décision

Une commande client est découpée en un dossier par fournisseur. La transmission
dépend d'un contrat commun et d'un adaptateur propre à chaque fournisseur ; elle
ne dépend jamais directement de CJ dans le modèle métier.

CJdropshipping est le premier adaptateur activé. Tant que le mode réel n'est pas
explicitement développé et autorisé, toute transmission CJ impose
`isSandbox=1`. Printful, BigBuy et tout fournisseur futur restent bloqués sans
adaptateur de commande explicite.

Le transport sélectionné est figé avec l'offre fournisseur car son nom est une
donnée obligatoire de la commande. Une clé stable empêche la retransmission
automatique d'un dossier déjà accepté. Une tentative incertaine ou échouée doit
être vérifiée avant toute relance.

### Conséquences

- une commande regroupant plusieurs fournisseurs produit plusieurs dossiers ;
- le moteur peut évoluer sans modifier la commande de pilotage ;
- le mode production est refusé par défaut ;
- le payload et la réponse fournisseur sont conservés pour audit ;
- le test CJ ne débite aucun solde et ne déclenche aucune expédition réelle.

## D012 — Séparer le suivi fournisseur du statut client

**Date :** 27 août 2026

**Statut :** Acceptée

### Décision

Le statut technique d'une commande fournisseur est conservé séparément du
statut métier de la commande client. Une synchronisation contrôlée traduit les
états fournisseur connus vers les états client `processing`, `shipped` et
`delivered`.

Le transporteur déjà sélectionné est conservé lorsqu'une réponse fournisseur
ultérieure ne le répète pas. Un numéro de suivi sandbox est toujours présenté
comme fictif et ne produit aucun lien de suivi actif. En production, un lien de
suivi peut être affiché lorsqu'un véritable numéro est disponible.

### Conséquences

- une variation du vocabulaire fournisseur ne fuit pas dans le domaine client ;
- l'opérateur conserve les informations techniques nécessaires à l'audit ;
- le client reçoit un statut simple et cohérent ;
- une synchronisation incomplète n'efface pas une donnée de transport connue ;
- la simulation ne peut pas être confondue avec une expédition réelle.

## D013 — Appliquer des règles douanières datées

**Date :** 27 août 2026

**Statut :** Acceptée

Le taux provisoire de 4 % est abandonné. Du 1er juillet 2026 au 30 juin
2028, un petit envoi hors UE vers l'UE, admissible et d'une valeur intrinsèque
n'excédant pas 150 EUR, supporte une estimation de 3 EUR par article.

La règle conserve sa méthode, sa date et sa source. Au-delà de 150 EUR, pour
les produits soumis à accise ou après expiration de la règle, le calcul bloque
au lieu d'inventer un taux. La TVA, les droits, l'IOSS et les frais de dossier
du transporteur restent des composantes distinctes. Une donnée inconnue reste
inconnue.

## D014 — Interdire les opportunités connues comme non rentables

**Date :** 27 août 2026

**Statut :** Acceptée

L'analyse fournisseur inclut la règle douanière avant de créer l'opportunité.
Elle bloque toute création lorsque le bénéfice calculé est inférieur à
0,01 EUR ou lorsque la marge sur vente nette est inférieure au seuil de sécurité
configuré, fixé par défaut à 10 %.

La publication effectue un second contrôle et refuse une marge connue négative
ou nulle. Cette protection couvre les coûts enregistrés ; les frais encore
inconnus restent signalés et doivent être confirmés avant le passage futur en
commande fournisseur réelle.

## D015 - Séparer les références visuelles des données fournisseur

**Date :** 14 septembre 2026

**Statut :** Acceptée

### Contexte

Les images issues des prix comparables dépendent déjà d'une offre fournisseur et ne constituent donc pas une référence indépendante pour décider si cette offre correspond à l'idée produit.

### Décision

Les références visuelles sont rattachées à `ProductIdea` et à chacun de ses `supplier_search_keywords`. Elles sont recherchées indépendamment des fournisseurs. Chaque `SupplierOffer` conserve le mot-clé qui a conduit à sa découverte et son image est comparée uniquement aux références associées à ce même mot-clé.

Cette qualification Vision est commune aux fournisseurs et au fallback économique CJ vers le stock CN. Les images des `ComparablePrice` restent des données aval et ne servent pas de référence primaire au matching fournisseur.

### Conséquences

Une offre `rejected`, ou non contrôlée alors que l'idée possède des références visuelles, ne poursuit pas vers la livraison, les prix comparables ou l'analyse financière. CJ, EPROLO, Printful, AW et les futurs fournisseurs peuvent utiliser la même étape générique de qualification visuelle.

### Documentation associée

Voir `ARCHITECTURE.md`.

## D016 - Calculer localement le shipping AW avant commande

**Date :** 14 septembre 2026

**Statut :** Acceptée

### Contexte

AW Dropship ne fournit pas de devis de livraison temps réel avant la création de commande. Le catalogue fournit en revanche le poids du SKU et AW communique une grille tarifaire statique par tranche de poids et par zone. Pour la France, AW indique également un jour ouvré maximum de préparation puis trois à cinq jours ouvrés de transport.

### Décision

`AWShippingEstimator` calcule localement le coût de livraison France à partir du poids total de la commande et de la grille AW connue. Le délai persiste comme une valeur prudente de 6 jours ouvrés, représentant la borne haute du délai total préparation comprise.

La méthode persistée reste générique sous le nom `AW Standard`. EcommerceIA ne déduit pas un transporteur précis comme Packeta, GLS ou DPD à partir de la seule tranche de poids tant qu'AW ne fournit pas de règle explicite de sélection.

### Conséquences

Une offre AW dont le poids est connu peut être analysée avant commande sans endpoint de devis temps réel. Une offre sans poids exploitable reste incomplète. Toute évolution future de la grille AW doit être datée, testée et documentée avant modification du calcul.

### Documentation associée

Voir `ARCHITECTURE.md`.

## D017 - Respecter le free shipping explicite de CJ

**Date :** 15 septembre 2026

**Statut :** Acceptée

### Contexte

Certaines offres CJ supplier-shipped indiquent explicitement que les frais de livraison sont inclus ou gratuits. Dans ce cas, l'API freight peut ne retourner aucun devis exploitable alors que l'absence de devis ne signifie pas que la livraison est indisponible.

### Décision

Le champ CJ `addMarkStatus` est normalisé en `free_shipping` sur `SupplierOffer` : `1` devient `True`, `0` devient `False` et l absence du champ reste inconnue. Une valeur inconnue ne doit jamais être assimilée à `False`.

Lorsque `free_shipping=True` et qu'aucun devis freight valide n'est retourné, `CJShippingEstimator` conserve l'offre avec un coût de livraison de 0 USD et la méthode `Free shipping included`. Le délai reste une donnée distincte et peut être recherché séparément via les informations logistiques disponibles.

### Conséquences

Une offre CJ explicitement en livraison gratuite ne doit pas être rejetée uniquement parce que l'API freight ne fournit aucun devis. Les anciennes offres CJ ont été backfillées à partir des données CJ disponibles ; les appels temporaires non résolus sont retentés sans inventer de valeur.

### Documentation associée

Voir `ARCHITECTURE.md`.


## D018 - Retirer CJ Europe du pipeline actif

**Date :** 22 septembre 2026

**Statut :** Acceptée

### Contexte

Le pipeline CJ avait été conçu avec une stratégie Europe-first : recherche dans les stocks européens, puis fallback vers la Chine lorsqu'aucune offre exploitable n'était trouvée.

Les investigations API menées en septembre 2026 ont montré que la présence d'un stock CJ réel en Europe, ou même l'existence d'une route théorique retournée par `freightCalculateTip`, ne garantit pas qu'une commande puisse réellement être créée vers les marchés cibles. Plusieurs produits disposant de `cjInventoryNum > 0` en Allemagne ont été testés vers la France. Les commandes Sandbox retournaient `logisticsMiss=True`, y compris lorsque DE-DHL ou DE-GLS apparaissaient lors du calcul de fret.

Les tests Free Shipping ont également montré que `addMarkStatus=1` ne garantit pas une livraison gratuite vers FR, BE ou ES. Le support CJ a confirmé qu'un freight template peut être limité à des lanes domestiques, par exemple DE->DE sans lane DE->FR.

Aucune variante testée avec stock CJ réel en Allemagne n'a fourni de lane DE->FR validée au niveau commande avec `logisticsMiss=False`.

### Décision

La recherche CJ Europe est retirée du pipeline métier actif.

Le flux CJ recherche désormais directement les offres en Chine (`CN`) pour les marchés cibles suivants :

- France (`FR`) ;
- Belgique (`BE`) ;
- Espagne (`ES`).

La stratégie `Europe -> fallback CN` n'est plus exécutée dans le pipeline.

Le code historique lié à `CJCountryFallbackService` peut être conservé hors flux actif afin de permettre une réévaluation future si CJ améliore ou clarifie ses capacités européennes.

### Conséquences

Le calcul du coût rendu CJ doit désormais être fiabilisé pour les flux `CN -> FR`, `CN -> BE` et `CN -> ES`.

Le chantier prioritaire devient le CJ Landed Cost : prix produit, transport, droits éventuels, TVA/IOSS et frais IOSS. Le chantier commande/facturation CJ vient ensuite.

CJ Europe et le Free Shipping DE->FR ne doivent plus bloquer les prochains développements.

### Documentation associée

Voir `ARCHITECTURE.md`, `ROADMAP.md` et `CHANGELOG.md`.

## D019 - Limiter le Briefing d Emma aux opportunites produites

**Date :** 24 septembre 2026

**Statut :** Acceptee

### Contexte

Le Briefing d Emma a ete concu pour presenter au commerçant les opportunites issues des travaux des assistants. L ajout de la possibilite de declencher manuellement les travaux normalement executes la nuit a progressivement introduit dans le Briefing des fonctions de pilotage du pipeline, puis d autres fonctions metier. Cette evolution risque de transformer le Briefing en tableau de bord general d EcommerceIA et de lui faire perdre sa fonction initiale.

### Decision

Le Briefing commence aux opportunites produites par les travaux des assistants. Il presente ces opportunites afin qu Emma puisse les examiner en vue de leur presentation au commerçant et de leur eventuelle publication dans la boutique EcommerceIA.

Le declenchement et le suivi des travaux des assistants, automatiques ou manuels, relevent du Pilotage et non du Briefing.

Les fonctions posterieures a la publication ou a l achat client, notamment commandes, paiement, traitement fournisseur, expedition et livraison, relevent des espaces metier responsables, notamment Gestion des commandes.

Une competence d Emma ou une action disponible pour Emma ne doit pas etre ajoutee au Briefing pour cette seule raison.

### Consequences

- la navigation principale de l espace Emma distingue notamment les menus Briefing, Pilotage et Gestion des commandes ;
- ces menus sont des fonctions distinctes de meme niveau dans la navigation et ne doivent pas etre fusionnes ;
- de nouvelles fonctions pourront etre ajoutees plus tard comme nouveaux menus lorsque leur responsabilite metier est distincte ;
- le Briefing reste centre sur la presentation et l examen des opportunites ;
- les commandes permettant de lancer ou suivre le pipeline sont placees dans le Pilotage ;
- les fonctions post-achat restent hors du Briefing ;
- tout nouveau besoin doit etre confronte a cette frontiere avant son ajout au Briefing ;
- les fonctions actuellement presentes dans le Briefing qui ne respectent pas cette frontiere doivent etre reaffectees a leur espace metier sans supprimer leur fonctionnalite.

### Documentation associee

Voir `EMMA.md`.

## D020 - Presenter les alertes dans leur espace metier

**Date :** 25 septembre 2026

**Statut :** Acceptee

### Contexte

Le commercant doit etre informe des situations qui necessitent son attention : stock insuffisant, paiement client ou fournisseur en attente, retard de traitement, retard d'expedition ou de livraison, incident dans les travaux des assistants et autres anomalies metier.

Creer un menu Alertes autonome obligerait le commercant a consulter un espace supplementaire et separerait l'alerte du contexte dans lequel il peut comprendre et traiter le probleme.

### Decision

Les alertes ne constituent pas un espace metier autonome dans la navigation d'Emma. Elles sont presentees dans l'espace metier auquel elles appartiennent.

Le Briefing ne presente que les alertes liees aux opportunites qu'Emma doit examiner. Le Pilotage presente les alertes liees aux travaux des assistants. Gestion des commandes presente les alertes liees notamment aux paiements, au traitement fournisseur, a l'expedition et a la livraison. Les futurs espaces metier appliqueront le meme principe.

La detection et la structuration des alertes peuvent etre centralisees dans un mecanisme transversal commun a Emma, sans centraliser leur presentation dans un menu unique.

Une alerte doit, lorsque cela est possible, conduire vers l'objet concerne et l'action permettant de traiter la situation.

### Consequences

- aucun menu Alertes boutique n'est cree pour cette fonction ;
- chaque espace affiche uniquement les alertes relevant de sa responsabilite ;
- la logique de detection peut etre mutualisee afin d'eviter les duplications ;
- une alerte doit conserver son contexte metier et permettre de rejoindre l'action appropriee ;
- les anciens composants d'alerte du Briefing doivent etre reevalues et reaffectes selon leur responsabilite metier plutot que supprimes automatiquement.

### Documentation associee

Voir `EMMA.md`.

