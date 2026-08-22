# Guide de développement

## Objectif

Ce document réunit les conventions de code, la stratégie de tests et la
définition commune d'un travail terminé.

## Méthode générale

Une évolution suit ce cycle :

1. clarifier le besoin utilisateur ;
2. identifier la règle métier ;
3. définir les responsabilités ;
4. écrire un test rouge ;
5. implémenter le comportement ;
6. obtenir le test vert ;
7. exécuter les tests du domaine ;
8. exécuter la suite complète ;
9. effectuer une recette visuelle ou manuelle ;
10. vérifier le diff et documenter la décision utile ;
11. créer un commit limité et explicite.

## Principes de code

- Une vue orchestre mais ne porte pas de logique métier complexe.
- Un service possède une responsabilité principale.
- Un modèle conserve les données et ses invariants proches.
- Un template affiche les informations reçues.
- Une URL représente une ressource ou une action métier compréhensible.
- Les dépendances externes sont isolées derrière des clients ou des services.
- Les traitements déterministes ne sont pas confiés à un modèle d'IA.
- Un composant doit pouvoir être résumé en une phrase.

## Services

La documentation d'un service doit permettre d'identifier :

- sa responsabilité ;
- ce qu'il ne fait pas ;
- ses entrées et sorties ;
- ses dépendances ;
- les composants qui l'utilisent.

Un service ne doit pas reproduire une règle dont un autre service est déjà
responsable.

## Templates

Chaque page doit avoir :

- un titre clair ;
- une action principale identifiable ;
- une navigation ou un retour approprié ;
- des messages orientés utilisateur ;
- un affichage utilisable sur ordinateur et mobile.

Lors d'une refonte importante, le fichier complet est réactualisé. Les ajouts
de fragments isolés dans un grand template sont évités lorsqu'ils risquent de
casser les blocs Django ou la structure HTML.

## Philosophie des tests

Un test protège un comportement utile, pas une ligne de code.

Chaque scénario doit pouvoir être lu ainsi :

```text
Étant donné une situation
Quand une action est exécutée
Alors le comportement métier attendu est observé
```

### Catégories

#### Tests de règles métier

Ils vérifient qu'une action est autorisée, refusée ou produit le bon changement
d'état.

#### Tests de calcul

Ils vérifient les formules de prix, marge, devise, stock ou expiration.

#### Tests de restitution

Ils vérifient que les vues et templates présentent les bonnes informations et
actions.

#### Tests d'intégration

Ils vérifient les contrats entre composants, en simulant les dépendances
externes lorsque le test ne doit pas contacter le réseau.

#### Tests de parcours

Ils couvrent les chaînes critiques : commande, paiement, récupération,
publication et décisions d'Emma.

## Règles de test

1. Toute nouvelle règle métier importante possède au moins un test.
2. Le test est écrit avant ou en même temps que l'implémentation.
3. Un test ne doit jamais dépendre involontairement d'une API réelle.
4. Une règle est testée dans le composant qui en est responsable.
5. Lorsqu'un test échoue, vérifier d'abord que le scénario décrit la bonne
   règle, puis vérifier le code.
6. Les dossiers de tests contiennent un `__init__.py` lorsque la découverte
   Django l'exige.
7. Le nombre de tests n'est pas l'objectif ; la couverture des comportements
   importants l'est.

## Commandes de validation

Test ciblé pendant le développement :

```bat
python manage.py test chemin.du.test.Classe.nom_du_test -v 2
```

Tests d'un domaine :

```bat
python manage.py test tests.orders -v 1
```

Suite complète :

```bat
python manage.py test -v 1 --failfast
```

Vérifications Django et migrations :

```bat
python manage.py check
python manage.py makemigrations --check --dry-run
```

Vérifications Git :

```bat
git diff --check
git diff --stat
git status --short
```

Après indexation :

```bat
git diff --cached --check
git diff --cached --stat
```

## Intégrations externes

- Les tests utilisent des mocks aux frontières HTTP, Stripe, OpenAI et e-mail.
- Les secrets restent dans les variables d'environnement.
- Une réponse externe est validée avant utilisation.
- Les erreurs de format, délais, quotas et authentification sont traitées.
- Les appels sont limités et journalisés.
- Un test ne doit pas réussir uniquement parce qu'une clé réelle est présente
  dans l'environnement local.

## Données et migrations

- Une modification de modèle est accompagnée de sa migration.
- Les migrations de données sont réversibles lorsque cela est raisonnable.
- Les identifiants externes et contraintes d'unicité évitent les doublons.
- Les scripts d'inspection temporaires ne sont pas ajoutés au dépôt sans avoir
  été transformés en commande ou test durable.

## Definition of Done

Une évolution est terminée lorsque :

- le comportement attendu est défini ;
- les tests ciblés sont verts ;
- les tests du domaine sont verts ;
- la suite complète est verte ;
- la recette manuelle pertinente est réalisée ;
- `git diff --check` ne signale rien ;
- les migrations sont cohérentes ;
- la documentation durable est mise à jour ;
- le commit ne contient pas de fichiers temporaires.
