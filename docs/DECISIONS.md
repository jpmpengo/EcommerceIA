Décision n°1
Pourquoi OpportunityAnalyzer ?

Pour séparer les calculs du modèle.

Décision n°2
Pourquoi OpportunityPublisher ?

Pour séparer la logique de publication de l'interface d'administration.

Décision n°3
Pourquoi Dashboard ?

Parce que le commerçant ne doit pas travailler dans Django Admin.

Décision n°4
Pourquoi Provider ?

Parce que nous voulons pouvoir remplacer FakeProvider
par Amazon, Alibaba, Temu ou un fichier Excel
sans modifier l'importeur.


# Décision 001

## Sujet

Création du Dashboard

## Contexte

Le commerçant utilisait Django Admin.

## Décision

Créer une application Dashboard qui devient
la porte d'entrée d'EcommerceIA.

## Conséquences

Le Dashboard est l'interface métier.

Django Admin reste un outil technique.


# Décision 002

## Sujet

Création d'OpportunityAnalyzer

...
# Décision n°005 : 
Créer DailyAssistant pour préparer la journée du commerçant.
Pourquoi ?

Parce que la vue ne doit jamais décider quoi dire.

Elle demande simplement au collaborateur :

"Qu'as-tu à me dire aujourd'hui ?

# Décision 006 – Création d'OpportunityAdvisor

Contexte : Les scores et les marges ne suffisent pas à expliquer une recommandation.

Décision : Créer un service OpportunityAdvisor chargé de transformer les données en recommandations compréhensibles.

Conséquences : EcommerceIA ne se contente plus de calculer, il explique ses décisions.

# Décision 007 – Création d'un Advisor

Un Advisor est créé lorsqu'un domaine métier devient suffisamment complexe pour justifier un spécialiste.