# Stratégie de tests

## Objectif

Garantir que les règles métier restent correctes
au fil des évolutions.

# Philosophie des tests

Un test ne vérifie pas simplement qu'une valeur est vraie.

Un test vérifie que le comportement attendu par une règle métier
est bien respecté.

Autrement dit :

- Un test décrit un scénario.
- Il exécute une action.
- Il vérifie que le résultat correspond au comportement attendu.

Exemple :

Scénario :
Une opportunité ne possède pas de catégorie.

Action :
Le commerçant demande sa publication.

Comportement attendu :
La publication est refusée avec une erreur.

Résultat du test :
✅ OK

Le « OK » signifie que le logiciel s'est comporté exactement comme
la règle métier l'exige.
---

## Tests unitaires

OpportunityAnalyzer

OpportunityAdvisor

BusinessAdvisor

OpportunityPublisher

RecommendationDecisionService

---

## Tests fonctionnels

Dashboard

Centre de recommandations

Catalogue

---

## Avant chaque sprint

python manage.py check

python manage.py test

| Service                       | Tests | Statut |
| ----------------------------- | ----: | :----: |
| OpportunityAnalyzer           |     2 |   🟢   |
| OpportunityPublisher          | 0 → 5 |   🟡   |
| OpportunityAdvisor            |     0 |    ⚪   |
| BusinessAdvisor               |     0 |    ⚪   |
| RecommendationDecisionService |     0 |    ⚪   |

## Que doit tester un test unitaire ?

Un test unitaire doit protéger une règle métier.

Il ne teste pas une ligne de code.

Il vérifie qu'une règle de gestion continue d'être respectée
après les évolutions du logiciel.

# Sprint 8.2

## Nom

Tests unitaires du service OpportunityPublisher

## Statut

✅ VALIDÉ

## Règles métier couvertes

- publication d'une opportunité valide
- catégorie obligatoire
- description obligatoire
- stock initial obligatoire
- statut "approved" obligatoire
- interdiction de publier deux fois la même opportunité

## Validation

- [x] python manage.py check
- [x] python manage.py test
- [x] 6 tests unitaires validés

# 1. Les tests protègent les règles métier

Un test unitaire doit protéger une règle métier. Il ne teste pas une ligne de code.

# 2. Un test décrit un scénario

Chaque test doit raconter une histoire.
Étant donné
une opportunité sans catégorie

Quand
je demande sa publication

Alors
la publication est refusée.

# Quand on lit le nom du test, on comprend immédiatement le scénario.

# Notre nouvelle philosophie :

# Un test protège une règle métier.

# On teste ce qui a de la valeur pour l'utilisateur, pas chaque ligne de code.

Par exemple :

Je ne vais pas tester que la méthode fait exactement cinq appels à la base de données.

En revanche, je vais tester que le commerçant voit bien les trois meilleures opportunités.

C'est cela qui a de la valeur.

# Classification des tests:

1. Tests de règles métier

Ils vérifient qu'une action est autorisée ou refusée.

Exemple :

Une opportunité doit être approuvée.

2. Tests de restitution

Ils vérifient que les bonnes informations sont présentées.

Exemple :

Le Dashboard reçoit les statistiques.

3. Tests de calcul

Ils vérifient les formules.

Exemple :

Le calcul de la marge.


# Comment écrire un test

Avant d'écrire un test, se poser les questions suivantes :

1. Quelle règle métier voulons-nous protéger ?

2. Quel est le scénario ?

   Étant donné...
   Quand...
   Alors...

3. Quel comportement est attendu ?

4. Que se passe-t-il si cette règle est cassée ?

Le test est ensuite écrit pour vérifier ce comportement.

## Quand un test échoue

Un test qui échoue ne signifie pas automatiquement
que le code est incorrect.

Il faut toujours se poser deux questions :

1. Le test décrit-il correctement la règle métier ?

2. Si oui, le code respecte-t-il cette règle ?

On ne modifie jamais le code avant d'avoir répondu
à ces deux questions.

# Règle DG-001

Toute nouvelle règle métier importante doit être accompagnée
d'au moins un test qui la protège.

Objectif :

- garantir la stabilité du logiciel ;
- éviter les régressions ;
- documenter le comportement attendu.

Le test doit être écrit avant ou en même temps que
l'implémentation de la règle métier.

# Règle DG-002

Avant d'écrire un test, identifier la règle métier.

Le test ne doit pas décrire une implémentation.

Le test doit décrire un comportement attendu.

# Règle DG-003

Quand un test échoue :

1. Vérifier que le test décrit correctement la règle métier.
2. Vérifier ensuite que le code respecte cette règle.
3. Ne jamais modifier le code avant d'avoir validé les deux points précédents.

## Réutilisation des règles métier

Une règle métier ne doit être testée qu'une seule fois
dans le service qui en est responsable.

Les autres services réutilisent cette règle
sans la redéfinir.

Chaque nouveau service ne teste que les comportements
dont il est responsable.
