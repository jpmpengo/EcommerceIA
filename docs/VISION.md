# EcommerceIA :
# Nous ne construisons pas une boutique en ligne. 
# Nous construisons un assistant qui aide un commerçant à prendre de meilleures décisions.
# Chaque fonctionnalité doit aider un commerçant à prendre une meilleure décision.
# Pendant que vous dormiez, EcommerceIA travaillait pour vous."
# ACCUEIL ne se contente jamais d'afficher des données.
# Faire en sorte qu'en ouvrant EcommerceIA le matin, le commerçant ait l'impression qu'un collaborateur lui parle, 
# et non qu'un logiciel lui affiche des statistiques.
# EcommerceIA n'est pas conçu pour montrer des données. Il est conçu pour aider un commerçant à prendre de meilleures décisions, 
# au bon moment, avec les bonnes explications.
# EcommerceIA ne remplace pas le commerçant. Il lui donne les moyens de prendre de meilleures décisions, plus rapidement
# et en comprenant toujours pourquoi. 

# Je pense que ces cinq documents formeront la colonne vertébrale du projet :

# BUSINESS.md → Pourquoi ?
# ROADMAP.md → Où allons-nous ?
# ARCHITECTURE.md → Comment est conçu le système ?
# PRINT_VALIDATION.md → Qu'est-ce qui est terminé ?
# CHANGELOG.md → Qu'est-ce qui a évolué ?

# Avec cette base, EcommerceIA sera non seulement un bon logiciel, mais aussi un projet agréable à faire évoluer et à transmettre.

# Il explique.

# Il conseille.

# Il propose une action.

# Chaque information doit aider le commerçant à décider.

# Je voudrais ajouter une onzième règle
# C'est peut-être la plus importante.
# Chaque nouveau composant doit pouvoir être expliqué en une phrase.
# Par exemple :

# Dashboard : prépare la journée du commerçant.
# BusinessAdvisor : choisit les priorités.
# RecommendationDecisionService : exécute la décision du commerçant.
# OpportunityPublisher : transforme une opportunité en produit.

# Si nous ne pouvons pas résumer un composant en une phrase, c'est souvent qu'il a trop de responsabilités.

# EcommerceIA aide le commerçant à prendre de meilleures décisions et les exécute avec lui.

## Vision

EcommerceIA est un assistant intelligent qui aide les commerçants à
prendre de meilleures décisions d'achat afin d'améliorer durablement
leur rentabilité.

Notre objectif n'est pas seulement de vendre des produits.

Notre objectif est d'aider le commerçant à choisir les bons produits,
au bon moment, auprès des bons fournisseurs.

---

# Notre promesse

Chaque jour, EcommerceIA analyse les opportunités du marché
et met en avant celles qui peuvent apporter le plus de valeur.

Le commerçant reste toujours le décideur.

EcommerceIA l'aide à décider.

---

# Nos principes

## Observer

Collecter les informations provenant de différents fournisseurs.

Amazon

Alibaba

Temu

Grossistes

Fichiers Excel

API

---

## Comprendre

Transformer les données en informations utiles.

Calcul des marges

Calcul des coûts

Analyse de la concurrence

Analyse de la demande

Détection des opportunités

---

## Conseiller

Expliquer pourquoi une opportunité est intéressante.

Le logiciel ne montre pas uniquement un score.

Il explique sa recommandation.

---

## Agir

Permettre au commerçant d'agir immédiatement.

Publier

Commander

Réapprovisionner

Archiver

---

# Notre architecture

Provider

↓

Importer

↓

Opportunity

↓

Analyzer

↓

Advisor

↓

Publisher

↓

Catalogue

↓

Vente

---

# Le Dashboard

Le Dashboard est l'interface principale.

Le commerçant commence toujours sa journée ici.

Le Dashboard doit répondre à quatre questions.

1. Comment va mon activité ?

2. Que dois-je savoir aujourd'hui ?

3. Que me conseille EcommerceIA ?

4. Que dois-je faire maintenant ?

---

# Django Admin

Le Django Admin est réservé aux opérations techniques.

Il sert à :

maintenance

configuration

gestion

correction des données

Le commerçant n'a normalement pas besoin de l'utiliser.

---

# Notre philosophie

Chaque information affichée doit aider le commerçant
à prendre une décision.

Chaque fonctionnalité doit apporter une valeur réelle.

Chaque évolution doit respecter cette vision.

---

# Notre objectif

Construire un assistant intelligent capable d'aider les commerçants
à identifier les meilleures opportunités commerciales
avant leurs concurrents.

Nous ne développons pas des fonctionnalités. 
Nous développons un assistant capable d'aider un commerçant à prendre de meilleures décisions.


# dashboard/
└── services/
    ├── emma_briefing_service.py        # Orchestre le briefing
    ├── emma_memory_service.py          # Dernière visite
    ├── emma_progress_service.py        # Ce que le commerçant a accompli
    ├── emma_attention_service.py       # Alertes importantes
    ├── priority_advisor.py             # Priorité du jour
    ├── emma_state_service.py           # Comprend la situation globale
    └── emma_summary_service.py         # Formule le discours d'Emma