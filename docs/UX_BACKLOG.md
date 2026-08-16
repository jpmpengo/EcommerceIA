# X-001

Observation

Le terme Mission est utilisé pour deux concepts différents.

Conséquence

Le commerçant hésite sur la différence.

Amélioration proposée

Ne conserver le mot Mission que pour l'objectif principal.

Renommer :

Missions du jour

par

Actions du jour

ou

Actions recommandées

# UX-001 — Vocabulaire du Dashboard

Écran : Dashboard

Observation

Le mot Mission est utilisé pour deux concepts différents :

Mission principale
Missions du jour

Ressenti

En tant que commerçant, je me demande quelle est la différence entre ces deux "missions".

Impact

🟡 Moyen à élevé

Ce n'est pas bloquant, mais cela crée une hésitation dès les premières secondes d'utilisation.

Piste d'amélioration

Conserver Mission pour l'objectif principal et renommer le second bloc :

📋 Actions du jour
📋 Actions recommandées
📋 À faire aujourd'hui

Personnellement, j'ai une préférence pour Actions du jour : c'est simple, concret et complémentaire à Mission principale.

# UX-002 — “Opportunités à examiner” concerne des opportunités détectées, mais le lien ouvre le Centre des recommandations approuvées.

# UX-003 / Évolution fonctionnelle

Observation

Le Dashboard mélange actuellement deux étapes du processus :

les opportunités à analyser ;
les recommandations prêtes à décider.

Conséquence

Le commerçant ne comprend pas pourquoi une mission annonce une opportunité alors que le Centre de recommandations est vide.

Évolution proposée

Créer un Centre d'analyse des opportunités distinct du Centre de recommandations.

# UX-005 — Répétition de l’analyse

Observation : la liste et la fiche détaillée affichent plusieurs informations identiques.

Proposition :

Sur la liste, conserver seulement :

nom ;
priorité ;
marge estimée ;
une ou deux raisons principales ;
boutons Examiner, Plus tard, Rejeter.

Sur la fiche détaillée, conserver l’analyse complète et les chiffres financiers.

Ainsi, le premier écran reste rapide à parcourir et le second devient clairement l’écran de décision.

# UX-006 — Après publication

Le message actuel est correct :

Produit publié avec succès.

Il pourrait devenir plus utile avec une action immédiate :

Produit publié avec succès. [Voir le produit]

Cela éviterait au commerçant de devoir chercher le produit nouvellement créé dans le catalogue.

# UX-007 — Harmoniser le vocabulaire

Utiliser Reporter partout.

Éviter de mélanger :

Plus tard
Reporter

# UX-008 — Confirmation plus informative

Au lieu de :

« La recommandation a été reportée pendant 14 jours. »

EcommerceIA pourrait dire :

"Recommandation reportée. Je vous la proposerai de nouveau le 18 août 2026."

Le collaborateur parle de façon plus naturelle.

# UX-009 — Deux niveaux d'analyse

Nous confirmons l'observation faite pendant le scénario "Publier".

Le premier écran sélectionne.

Le deuxième aide à décider.

Nous pourrons alléger le premier écran lors du futur Sprint UX.

## UX-003 — Séparer analyse et recommandation

### Problème

Le Dashboard annonce des opportunités à analyser,
mais le bouton ouvre le Centre de recommandations,
qui ne contient que les opportunités approuvées.

### Conséquence

Le commerçant arrive sur une page vide
alors qu’une action lui avait été annoncée.

### Solution cible

Créer un Centre d’analyse des opportunités
pour les statuts :

- detected
- review

Le Centre de recommandations reste réservé aux opportunités :

- approved
- non publiées
- non reportées

### Priorité

🔴 Élevée


# Emma parle avant que les chiffres parlent.