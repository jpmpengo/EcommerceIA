# Roadmap d'EcommerceIA

## Règle de lecture

Cette roadmap décrit des priorités, pas des dates contractuelles. Une phase ne
devient automatique qu'après validation de son fonctionnement manuel ou
assisté.

## Fondations validées

### Boutique

- catalogue et catégories ;
- fiches produit ;
- panier ;
- commande invitée ;
- réservation temporaire du stock ;
- paiement Stripe en environnement de test ;
- confirmation idempotente et diminution du stock après paiement ;
- historique et détail des commandes ;
- récupération sécurisée des commandes par e-mail ;
- création de compte après achat ;
- rattachement des commandes au compte ;
- modification du mot de passe.

### Intelligence produit

- observations de marché ;
- fournisseurs et offres fournisseur ;
- clients CJdropshipping et Printful ;
- conversion de devise ;
- estimation de livraison ;
- extraction de dimensions, capacité et autres caractéristiques ;
- comparaison de produits comparables ;
- calcul et création d'opportunités ;
- publication avec traçabilité.

### Qualité

- suite de tests automatisés ;
- tests de réservation, paiement, récupération et comptes ;
- séparation des services métier ;
- historique Git par lots fonctionnels.

## Priorité 1 — Consolider l'espace Emma

Objectifs :

- appliquer à Emma le niveau de finition visuelle de la boutique ;
- distinguer clairement l'espace commerçant de l'espace internaute ;
- présenter les priorités, statuts et actions de façon cohérente ;
- simplifier les écrans d'opportunité ;
- vérifier les permissions d'accès ;
- valider l'affichage sur ordinateur et mobile.

## Priorité 2 — Prototype de découverte produit

Objectifs :

- introduire le concept d'idée produit ;
- définir le contexte commercial envoyé à OpenAI ;
- obtenir une sortie structurée et sourcée ;
- limiter une génération à dix idées ;
- permettre à Emma d'en sélectionner trois au maximum ;
- conserver la traçabilité de la génération.

La stratégie de référence est `PRODUCT_DISCOVERY.md`.

## Priorité 3 — Recherche marketplace ciblée

Objectifs :

- transformer une idée sélectionnée en requêtes précises ;
- imposer les limites de pages et de résultats ;
- dédupliquer les annonces ;
- produire une observation synthétique ;
- afficher la source, la date et le niveau de confiance ;
- mesurer les volumes et temps de traitement.

## Priorité 4 — Validation fournisseur

Objectifs :

- rechercher des offres uniquement pour les idées validées ;
- comparer les variantes réellement comparables ;
- intégrer prix, devise, stock, livraison et délai ;
- sélectionner ou valider une offre fournisseur ;
- empêcher la publication sans offre acceptable.

## Priorité 5 — Boucle de décision et publication

Objectifs :

- présenter une recommandation expliquée ;
- distinguer calculs certains, estimations et interprétations ;
- conserver l'humain dans la boucle ;
- publier avec une traçabilité complète ;
- relier les résultats commerciaux à l'idée d'origine.

## Priorité 6 — Exploitation et automatisation

À envisager seulement après validation locale :

- traitement périodique des réservations expirées ;
- files de tâches et Celery ;
- planification des recherches ;
- quotas par source ;
- surveillance des erreurs API ;
- archivage des observations anciennes ;
- stockage durable des images ;
- notifications ;
- approvisionnement assisté puis automatisé ;
- suivi fournisseur et livraison.

## Backlog UX conservé

- employer « Actions du jour » plutôt que plusieurs sens de « Mission » ;
- séparer Centre d'analyse et Centre de recommandations ;
- alléger les listes et réserver les détails aux fiches ;
- afficher une action « Voir le produit » après publication ;
- employer « Reporter » de manière cohérente ;
- afficher la date de réapparition d'une recommandation reportée ;
- faire parler Emma avant les chiffres.

## Hors périmètre immédiat

- import complet d'un catalogue marketplace ;
- publication autonome par l'IA ;
- commande fournisseur automatique ;
- déploiement de Celery avant nécessité mesurée ;
- apprentissage automatique à partir d'un historique insuffisant.
