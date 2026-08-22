from dashboard.services.access_service import (
    DashboardAccessService,
)


def emma_access(request):
    return {
        "can_access_emma": (
            DashboardAccessService.can_access(
                request.user
            )
        ),
    }