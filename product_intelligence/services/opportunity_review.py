class OpportunityReviewService:

    def approve(
        self,
        opportunity,
    ):
        if opportunity.status != "review":
            raise ValueError(
                "Only opportunities in review can be approved."
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