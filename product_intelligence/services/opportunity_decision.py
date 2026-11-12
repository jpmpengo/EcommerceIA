class OpportunityDecisionService:

    def __init__(
        self,
        minimum_score=None,
    ):
        self.minimum_score = minimum_score

    def evaluate(
        self,
        opportunity,
    ):
        if (
            self.minimum_score is not None
            and opportunity.opportunity_score is not None
            and opportunity.opportunity_score
            >= self.minimum_score
        ):
            opportunity.status = "review"
            opportunity.save(
                update_fields=[
                    "status",
                    "opportunity_score",
                    "updated_at",
                ]
            )

        return opportunity

    