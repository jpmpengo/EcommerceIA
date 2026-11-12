class OpportunityReviewService:

    def approve(
        self,
        opportunity,
    ):
        if opportunity.status != "review":
            raise ValueError(
                "Only opportunities in review can be approved."
            )

        if not opportunity.market_collection_batch_id:
            raise ValueError(
                "Approbation refusée : aucun lot de prix comparables "
                "n’est associé à cette opportunité."
            )

        if opportunity.demand_score <= 0 or opportunity.competition_score <= 0:
            raise ValueError(
                "Approbation refusée : les données de demande et de concurrence "
                "doivent être complétées avant recommandation."
            )

        opportunity.status = "approved"

        opportunity.save(
            update_fields=[
                "status",
                "opportunity_score",
                "updated_at",
            ]
        )

        return opportunity

    def reject(
        self,
        opportunity,
    ):
        if opportunity.status != "review":
            raise ValueError(
                "Only opportunities in review can be rejected."
            )

        opportunity.status = "rejected"

        opportunity.save(
            update_fields=[
                "status",
                "opportunity_score",
                "updated_at",
            ]
        )

        return opportunity