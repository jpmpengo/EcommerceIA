# Changelog

Ce document résume les lots fonctionnels validés. Git conserve le détail des
modifications et `JOURNAL.md` conserve les notes de travail.



## 22 septembre 2026

### Simplification du pipeline CJ

- retrait de la recherche CJ Europe du pipeline métier actif ;
- recherche CJ désormais directe depuis la Chine (`CN`) ;
- marchés cibles conservés : France (`FR`), Belgique (`BE`) et Espagne (`ES`) ;
- abandon du mécanisme actif `Europe -> fallback CN` ;
- conservation éventuelle du code historique Europe/fallback hors du flux réel ;
- correction de la règle Free Shipping : `free_shipping=True` ne suffit pas à prouver un coût de livraison nul vers une destination ;
- `postageAmount=0` avec `logisticsMiss=True` est traité comme une absence de logistique assignée, pas comme une livraison gratuite ;
- priorité suivante : chantier CJ Landed Cost `CN -> FR/BE/ES` ;
- chantier suivant : commande et facturation CJ.
\n## Août 2026

### Documentation consolidée

- réduction de la documentation à huit références et deux historiques ;
- clarification des responsabilités documentaires ;
- formalisation de la stratégie de découverte produit ;
- définition du rôle d'OpenAI, des marketplaces, des fournisseurs et d'Emma ;
- définition des garde-fous de volume et de traçabilité.

### Comptes et commandes invitées

- commande possible sans compte ;
- accès sécurisé aux commandes de la session ;
- récupération des commandes par code temporaire envoyé par e-mail ;
- préremplissage de l'inscription depuis la commande ;
- rattachement des commandes au nouveau compte lorsque l'adresse correspond ;
- unicité insensible à la casse des adresses de comptes ;
- modification du mot de passe avec maintien de la session.

### Paiement et stock

- intégration Stripe en environnement de test ;
- retour stable après paiement ;
- confirmation de paiement idempotente ;
- diminution du stock après paiement confirmé ;
- réservation temporaire avant paiement ;
- expiration et libération du stock réservé.

### Boutique

- refonte visuelle de l'accueil public ;
- refonte du catalogue et des fiches produit ;
- refonte du panier, de la commande et des écrans de confirmation ;
- ajout et harmonisation des images produit ;
- distinction entre parcours public et espace commerçant.

### Intelligence produit

- intégrations CJdropshipping et Printful ;
- comparaison multi-fournisseur ;
- estimation des frais de livraison ;
- conversion des devises ;
- extraction et persistance des caractéristiques de variantes ;
- comparaison par dimensions et capacité ;
- traçabilité entre observation, offre, opportunité et produit publié.

### Décision commerciale

- Dashboard comme interface métier ;
- analyse et explication des opportunités ;
- publication, report et rejet ;
- report automatique pendant 14 jours ;
- séparation entre calcul, conseil, décision et exécution.

### Parcours bout en bout du 27 août 2026

- validation de l'idée 16 jusqu'à la publication du produit 16 ;
- achat par un compte client distinct et paiement Stripe de test ;
- diminution idempotente du stock de 10 à 9 ;
- affichage de l'adresse de livraison côté client et opérateur ;
- préparation financière et douanière provisoire du dossier fournisseur ;
- vérification en lecture seule de la variante CJ Black-2XL ;
- transmission de la commande 21 à CJ en sandbox ;
- confirmation, paiement et cycle logistique simulés jusqu'à `DELIVERED` ;
- synchronisation du statut client, du transporteur et du suivi ;
- distinction visible entre suivi fictif sandbox et suivi réel.

### Règles douanières datées

- remplacement du taux provisoire de 4 % ;
- droit temporaire de 3 EUR par article pendant la période réglementaire ;
- blocage lorsque le code tarifaire ou une nouvelle règle est nécessaire ;
- distinction entre TVA, droits, IOSS et frais de dossier ;
- recalcul du test : droits 3,00 EUR, charges 9,92 EUR et marge 2,57 EUR.

### Protection contre la vente à perte

- calcul douanier intégré avant la création d'une opportunité ;
- bénéfice minimal connu de 0,01 EUR ;
- seuil de sécurité configurable, fixé par défaut à 10 % de la vente nette ;
- blocage explicite des opportunités non rentables ;
- second contrôle déterministe immédiatement avant publication ;
- conservation des avertissements sur les coûts encore inconnus.

## Historique initial

### 27 août 2026 — Commande fournisseur générique

- dossiers fournisseurs séparés par fournisseur ;
- contrat et fabrique d'adaptateurs de commande ;
- adaptateur CJ limité au sandbox avec `isSandbox=1` obligatoire ;
- protection contre les doubles transmissions ;
- conservation du mode de transport, du payload et de la réponse fournisseur ;
- commande `submit_supplier_order` et couverture de tests dédiée.
- lecture des commandes CJ sandbox et conservation des statuts/suivis ;
- simulation du paiement, des statuts et d'un numéro de suivi fictif ;
- commande `manage_supplier_order_sandbox`, inaccessible au mode réel.
- confirmation CJ explicite entre `CREATED` et `UNPAID` ;
- propagation contrôlée des statuts fournisseur vers la commande client ;
- conservation du transporteur lorsque CJ ne le renvoie plus ;
- présentation séparée du dossier fournisseur dans le back-office.

### Sprint 9.1

- report d'une recommandation approuvée pendant 14 jours ;
- conservation sans création de produit ;
- retour automatique après expiration ;
- validation technique du parcours.

### Sprint 8.2

- couverture des règles d'`OpportunityPublisher` ;
- protection de la catégorie, description, stock, statut et publication unique.

### Sprint 7.9

- audit des principaux services métier ;
- clarification de leurs responsabilités et dépendances.

### Sprint 7.2.1

- publication d'une recommandation ;
- création et liaison du produit ;
- changement de statut et confirmation utilisateur.

### Sprint 7.1

- Dashboard enrichi ;
- liste et détail des recommandations ;
- analyse financière et navigation métier.
