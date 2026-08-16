# Toute décision prise par EcommerceIA doit pouvoir être expliquée.

Elle s'appliquera :

à OpportunityAdvisor ;
à BusinessAdvisor ;
à PricingAdvisor ;
à StockAdvisor ;
et même au futur CEOAdvisor.

# Répond à une seule question :

# Pourquoi EcommerceIA existe ?

Il contient :

la vision du produit ;
les règles métier ;
le rôle des Advisors ;
le rôle des Executors ;
les objectifs fonctionnels.

Il évolue lentement.

Aujourd’hui, le score ajoute :

40 points pour la marge
30 points pour la demande
20 points pour la concurrence

90 points

Ce n’est pas une erreur bloquante, mais c’est incohérent : le score ne peut jamais atteindre 100 avec les règles actuelles.

Nous avons deux possibilités :

accepter officiellement un score maximal de 90 ;
ajouter plus tard un quatrième critère de 10 points.

# OpportunityAnalyzer

C'est lui qui est à l'origine de toute la chaîne de décision.

Nous avons donc potentiellement deux responsabilités dupliquées.

C’est le principal point d’attention de cet audit.


Conclusion de l’audit
Question	Résultat
Responsabilité claire	✅
Nom pertinent	✅
Méthodes lisibles	✅
Réutilisable	✅
Duplication possible	⚠️ recommended_price()
Incohérence métier	⚠️ score maximal de 90

Je propose de ne pas modifier immédiatement OpportunityAnalyzer.

La prochaine validation doit être très ciblée : rechercher où get_recommended_price() est défini et utilisé. Ensuite, nous déciderons d’un seul emplacement officiel pour cette règle métier.

## Opportunités

Le Centre de recommandations et le Dashboard
peuvent ne contenir aucune opportunité.

L'absence d'opportunité n'est pas une erreur.

Elle signifie simplement qu'aucune opportunité
ne satisfait actuellement les critères métier
du commerçant.

# EcommerceIA ne recommande jamais un produit uniquement pour remplir une liste.


## BR-001 - Opportunités

Le Dashboard peut ne présenter aucune opportunité.

Cette situation est normale.

Elle signifie qu'aucune opportunité ne satisfait
actuellement les critères de sélection définis
par EcommerceIA.
