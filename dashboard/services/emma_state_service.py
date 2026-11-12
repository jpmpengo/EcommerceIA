class EmmaState:
    REVIEW_REQUIRED = "review_required"
    ALL_CLEAR = "all_clear"


class EmmaStateService:

    @staticmethod
    def get_state(review_opportunities_count):
        if review_opportunities_count > 0:
            return EmmaState.REVIEW_REQUIRED

        return EmmaState.ALL_CLEAR
