class OpportunityReviewContext:
    @staticmethod
    def build(completed_studies, requested_complements, completion_results):
        return (
            "REEVALUATION CIBLEE APRES COMPLEMENTS.\n"
            "Etudes deja realisees : " + str(completed_studies) + "\n"
            "Demandes precedentes : " + str(requested_complements) + "\n"
            "Resultats des assistants : " + str(completion_results) + "\n"
            "Ne recommence pas une etude terminee sans contradiction factuelle nouvelle, precise et verifiable. "
            "Evalue les resultats obtenus et distingue risque confirme, incertitude secondaire et information essentielle manquante. "
            "Choisis recommend si le dossier est suffisamment etaye et viable, reject si les resultats demontrent une non-viabilite, "
            "ou study uniquement si une information essentielle reste reellement manquante. "
            "Pour chaque demande precedente, examine si le resultat apporte une reponse suffisante, partielle ou defavorable. "
            "Une etude terminee avec un resultat defavorable constitue un risque commercial, pas automatiquement un motif de nouvelle recherche. "
            "Ne rouvre jamais une etude financiere, commerciale ou logistique deja traitee pour obtenir simplement davantage de details. "
            "Toute nouvelle demande portant sur une etude terminee doit identifier une contradiction factuelle nouvelle, precise et verifiable, expliquer son impact sur la decision et fournir une action de resolution ciblee. "
            "Si aucune contradiction nouvelle ne justifie la reouverture, utilise les conclusions existantes. "
            "Cette reevaluation clot le cycle de complements deja demandes. "
            "Ne transforme pas un resultat negatif, partiel ou non concluant en une nouvelle demande identique. "
            "Si les preuves confirment une opportunite viable, choisis recommend. "
            "Si les risques ou les incertitudes residuelles empechent de soutenir raisonnablement le produit, choisis reject. "
            "Ne conserve study que pour un obstacle essentiel nouveau, precis et resoluble, non deja traite par les assistants. "
            "Les calculs financiers existants font foi pour cette reevaluation. "
            "Ne force jamais une recommandation favorable."
        )
