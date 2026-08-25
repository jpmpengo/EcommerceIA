# Roadmap d'EcommerceIA

## Règle de lecture

Cette roadmap décrit des priorités, pas des dates contractuelles. Une phase ne
devient automatique qu'après validation de son fonctionnement manuel ou
assisté.

Chaque priorité doit être développée par petits lots testés. Une nouvelle phase
ne doit pas supprimer les données ou services historiques avant que leur
remplacement soit fonctionnel et vérifié.

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

- fournisseurs et offres fournisseur ;
- clients CJdropshipping et Printful ;
- conversion de devise ;
- estimation de livraison ;
- extraction de dimensions, capacité et autres caractéristiques ;
- comparaison de produits comparables ;
- calcul et création d'opportunités ;
- publication avec traçabilité ;
- génération manuelle de cinq idées structurées avec OpenAI ;
- présentation et sélection des idées dans l'espace Emma ;
- prototype historique d'étude Etsy.

Le prototype Etsy a permis de vérifier l'orchestration technique, mais il ne
constitue plus l'architecture cible. Une marketplace spécialisée ne permet pas
de valider correctement toutes les catégories de produits.

### Qualité

- suite de tests automatisés ;
- tests de réservation, paiement, récupération et comptes ;
- séparation des services métier ;
- historique Git par lots fonctionnels ;
- calculs déterministes séparés des explications générées par OpenAI.

## Changement de cap adopté

Les intégrations directes aux marketplaces sont abandonnées pour le parcours de
découverte produit.

Le nouveau parcours cible est :

```text
recherche web sourcée
  -> cinq catégories prometteuses
  -> produits fournisseurs
  -> préqualification
  -> prix comparables recherchés sur le Web
  -> calculs et scores
  -> validation par Emma et le commerçant
```

La stratégie détaillée est définie dans `PRODUCT_DISCOVERY.md`. La décision est
consignée dans `DECISIONS.md`.

## Priorité 1 — Sécuriser la transition

Objectifs :

- identifier les modèles, services, vues, routes et tests liés aux études de
  marketplaces ;
- distinguer le code historique du code encore utilisé ;
- conserver ou migrer les données historiques utiles ;
- empêcher le lancement de nouvelles études marketplace ;
- retirer progressivement les écrans et actions devenus obsolètes ;
- conserver la suite de tests verte après chaque suppression ;
- ne supprimer les anciens modèles qu'après mise en place de leurs remplaçants.

Cette priorité ne doit pas être réalisée par une suppression massive. Chaque
lot doit être vérifiable et réversible par Git.

## Priorité 2 — Découvrir cinq catégories sourcées

Objectifs :

- remplacer la notion d'idée isolée par une catégorie prometteuse documentée ;
- définir le contexte commercial envoyé à OpenAI ;
- activer une recherche web limitée ;
- demander exactement cinq catégories par campagne ;
- exiger des sources et leur date ;
- distinguer les faits, les hypothèses et les incertitudes ;
- interdire les chiffres de ventes inventés ;
- produire une sortie structurée et validée ;
- conserver la traçabilité de la génération ;
- permettre à Emma de présenter les catégories au commerçant.

Une catégorie sans preuve suffisante reste une hypothèse et ne doit pas être
présentée comme une meilleure vente certaine.

## Priorité 3 — Rechercher les produits fournisseurs

Objectifs :

- transformer chaque catégorie en requêtes fournisseur précises ;
- interroger uniquement les fournisseurs configurés et accessibles ;
- récupérer au maximum cinq produits par catégorie et par fournisseur ;
- normaliser les prix, devises, stocks, variantes et disponibilités ;
- intégrer le pays, les frais et le délai de livraison ;
- rapprocher les produits réellement comparables ;
- conserver l'identifiant et l'URL du produit fournisseur ;
- dédupliquer les produits ;
- ne jamais inventer une donnée absente.

La présence d'un produit chez un fournisseur ne suffit pas à créer une
opportunité.

## Priorité 4 — Préqualifier les candidats

Objectifs :

- calculer la complétude des données fournisseur ;
- écarter les produits indisponibles ou sans prix exploitable ;
- comparer le stock, le coût, les frais et le délai de livraison ;
- calculer un premier score de similarité avec la catégorie ;
- expliquer chaque exclusion ;
- conserver au maximum dix candidats pour la recherche approfondie.

La préqualification évite de payer des recherches web pour des produits déjà
inexploitables.

## Priorité 5 — Rechercher les prix comparables

Objectifs :

- utiliser une recherche web sourcée sans connexion directe aux marketplaces ;
- rechercher jusqu'à cinq prix comparables par candidat ;
- conserver le produit, le vendeur, le prix, la devise, l'URL et la date ;
- conserver les frais de livraison lorsqu'ils sont disponibles ;
- mesurer la similarité entre le résultat et le produit fournisseur ;
- rejeter les résultats sans URL vérifiable ;
- ignorer les produits insuffisamment comparables ;
- normaliser les devises ;
- dédupliquer les observations ;
- mesurer le coût et la durée des recherches.

Une page de marketplace peut apparaître comme source publique sans que
EcommerceIA utilise son API développeur.

## Priorité 6 — Calculer et expliquer les opportunités

Objectifs :

- calculer le prix concurrent médian ;
- mesurer la dispersion des prix ;
- calculer le coût livré estimé ;
- calculer la marge brute et la marge estimée ;
- calculer les scores de marge, stock, livraison, similarité et confiance ;
- distinguer les données connues, manquantes et estimées ;
- empêcher une donnée inconnue d'être interprétée comme zéro ;
- produire un score global reproductible ;
- faire expliquer les résultats par OpenAI sans lui confier les calculs.

Tous les calculs de référence restent déterministes et couverts par des tests.

## Priorité 7 — Adapter la validation par Emma

Objectifs :

- présenter les catégories et leurs sources ;
- présenter le produit fournisseur et ses caractéristiques ;
- afficher les prix comparables avec leurs URLs et dates ;
- afficher les marges, scores et données manquantes ;
- expliquer les risques et le niveau de confiance ;
- proposer les actions « Retenir », « Reporter » et « Écarter » ;
- conserver l'historique des décisions ;
- empêcher toute publication sans validation humaine et offre acceptable.

Emma conseille et présente. Le commerçant conserve la décision finale.

## Priorité 8 — Publication contrôlée et retour d'expérience

Objectifs :

- publier uniquement une opportunité validée ;
- conserver une traçabilité complète entre catégorie, fournisseur, observations,
  opportunité et produit ;
- relier les résultats commerciaux à la catégorie d'origine ;
- mesurer les écarts entre les prévisions et les résultats réels ;
- améliorer progressivement les règles déterministes ;
- ne pas transformer automatiquement un résultat commercial en nouvelle règle.

## Priorité 9 — Exploitation et automatisation

À envisager seulement après validation locale du parcours complet :

- traitement périodique des réservations expirées ;
- files de tâches et Celery ;
- planification des campagnes de recherche ;
- quotas par fournisseur et source web ;
- surveillance des erreurs API et de recherche ;
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
- faire parler Emma avant les chiffres ;
- afficher clairement les sources, dates et données manquantes ;
- distinguer une hypothèse, un candidat fournisseur et une opportunité.

## Hors périmètre immédiat

- intégration directe à une marketplace ;
- import complet d'un catalogue externe ;
- affirmation certaine des cinq meilleures ventes du marché ;
- publication autonome par l'intelligence artificielle ;
- commande fournisseur automatique ;
- décision commerciale entièrement automatisée ;
- déploiement de Celery avant nécessité mesurée ;
- apprentissage automatique à partir d'un historique insuffisant ;
- remplacement des données absentes par des estimations non signalées.

## Critères de validation du nouveau parcours

Le changement de cap sera considéré comme fonctionnel lorsque :

- cinq catégories structurées et sourcées peuvent être générées ;
- les produits fournisseurs sont récupérés sans donnée inventée ;
- dix candidats maximum sont préqualifiés de manière explicable ;
- chaque prix comparable retenu possède une URL et une date ;
- les calculs et scores sont reproductibles ;
- les données manquantes restent visibles ;
- Emma permet de retenir, reporter ou écarter chaque opportunité ;
- aucune intégration directe à une marketplace n'est nécessaire au parcours.
