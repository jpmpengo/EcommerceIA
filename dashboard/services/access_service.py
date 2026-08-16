class DashboardAccessService:

    EMMA_GROUP_NAME = "Emma Operators"

    @staticmethod
    def can_access(user):
        if not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        return user.groups.filter(
            name=DashboardAccessService.EMMA_GROUP_NAME
        ).exists()

        