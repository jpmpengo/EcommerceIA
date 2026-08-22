# Changelog

Ce document résume les lots fonctionnels validés. Git conserve le détail des
modifications et `JOURNAL.md` conserve les notes de travail.

## Août 2026

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

## Historique initial

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
