# Journal du projet

Le journal conserve des jalons humains et des réflexions datées. Les règles
durables sont transférées dans les documents de référence.

## 22 août 2026 — Origine des idées produit

La réflexion sur les volumes des marketplaces a conduit à reformuler le point
d'entrée de Product Intelligence.

Le projet ne doit pas demander des catalogues complets à eBay, Etsy, CJ ou
Printful. OpenAI peut proposer une courte liste d'idées sourcées ; Emma en
sélectionne quelques-unes ; les API réelles apportent ensuite les preuves de
marché et de faisabilité.

La règle retenue est : formuler d'abord une hypothèse limitée, puis collecter
uniquement les données nécessaires à sa vérification.

Cette décision est formalisée dans `PRODUCT_DISCOVERY.md` et `DECISIONS.md`.

## 21 août 2026 — Parcours après paiement

Le paiement Stripe en environnement de test a été validé avec confirmation de
la commande et diminution du stock. Le parcours invité permet maintenant de
retrouver une commande, puis de créer un compte et de lui rattacher les
commandes correspondantes.

## Août 2026 — Boutique professionnelle

Les principaux templates publics ont été réactualisés : accueil, catalogue,
fiche produit, panier, commande, confirmation et historique. La boutique et
Emma sont désormais considérées comme deux expériences distinctes à harmoniser
sans les confondre.

## 1 août 2026 — Naissance de l'accueil métier

EcommerceIA accueille pour la première fois le commerçant avec un message
personnalisé. Le Dashboard devient la porte d'entrée métier et Django Admin
reste l'outil d'administration technique.

`OpportunityPublisher` est séparé de l'interface afin de protéger la logique de
publication.
