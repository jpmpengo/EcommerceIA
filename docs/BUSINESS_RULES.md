# BUSINESS_RULES.md

## BR-001 — Absence d'opportunité

Le Dashboard peut ne présenter aucune opportunité.

Cette situation est normale.

Elle signifie qu'aucune opportunité ne répond
actuellement aux critères de sélection.

---

## BR-002 — Publication

Une opportunité doit être approuvée avant
de pouvoir être publiée.

---

## BR-003 — Données obligatoires

Une opportunité ne peut être publiée que si :

- une catégorie est définie ;
- une description est renseignée ;
- un stock initial est supérieur à zéro.

---

## BR-004 — Publication unique

Une opportunité déjà publiée
ne peut pas être publiée une seconde fois.

---

## BR-005 — Dashboard

Le Dashboard présente au maximum
les trois opportunités prioritaires.

## BR-006 — Report d’une recommandation

Le commerçant peut demander à traiter une recommandation plus tard.

Il n’a pas à choisir la date de réapparition.

EcommerceIA masque automatiquement la recommandation pendant 14 jours.

Pendant cette période :

- la recommandation reste conservée ;
- aucun produit n’est créé ;
- elle n’apparaît pas dans les recommandations prioritaires.

À l’issue des 14 jours, elle redevient éligible à l’analyse.

Principe :

Le commerçant exprime l’intention.
EcommerceIA conduit l’exécution de la décision.

# Règle métier (BR-006)

Une opportunité approuvée peut être reportée pendant 14 jours sans être publiée.

Une belle règle métier

Je l'écrirais ainsi :

# Une opportunité rejetée ne réapparaît jamais. 
En revanche, une nouvelle opportunité concernant le même produit peut être créée si les conditions de marché évoluent de manière significative.
