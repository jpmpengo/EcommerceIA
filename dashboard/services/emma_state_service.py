
class EmmaState:
    ACTION_REQUIRED = "action_required"
    PREPARATION_REQUIRED = "preparation_required"
    ALL_CLEAR = "all_clear"


class EmmaStateService:

    @staticmethod
    def get_state(
        progress,
        priority,
        alerts,
        preparation,
    ):

        if priority:
            return EmmaState.ACTION_REQUIRED

        if alerts:
            return EmmaState.ACTION_REQUIRED

        if preparation:
            return EmmaState.PREPARATION_REQUIRED

        return EmmaState.ALL_CLEAR

   
        