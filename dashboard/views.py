from .services.assistant import DailyAssistant

from dashboard.services.emma_briefing_service import (
    EmmaBriefingService,
)

from django.contrib.auth.decorators import login_required

from dashboard.services.business_advisor import BusinessAdvisor

from django.shortcuts import render, redirect

from django.shortcuts import get_object_or_404

from product_intelligence.models import ProductOpportunity
from product_intelligence.services.opportunity_review import (
    OpportunityReviewService,
)

from dashboard.services.access_service import (
    DashboardAccessService,
)

@login_required
def home(request):
    if not DashboardAccessService.can_access(
        request.user
    ):
        return redirect(
            "products:product_list"
        )

    advisor = BusinessAdvisor()
    brief = advisor.get_business_brief()

    briefing = EmmaBriefingService.build(
        request.user
    )

    review_opportunities = (
        ProductOpportunity.objects.filter(
            status="review",
        )
        .order_by(
            "-opportunity_score",
            "-detected_at",
        )
    )

    return render(
        request,
        "dashboard/home.html",
        {
            "brief": brief,
            "briefing": briefing,
            "review_opportunities": review_opportunities,
        },
    )

@login_required
def approve_opportunity(request, opportunity_id):
    
    if not DashboardAccessService.can_access(
        request.user
    ):
        return redirect(
            "products:product_list"
        )

    opportunity = get_object_or_404(
        ProductOpportunity,
        id=opportunity_id,
    )

    if request.method != "POST":
        return redirect(
            "dashboard:home"
        )

    service = OpportunityReviewService()

    service.approve(
        opportunity
    )

    return redirect(
        "dashboard:home"
    )

@login_required
def reject_opportunity(request, opportunity_id):
    if not request.user.is_staff:
        return redirect(
            "products:product_list"
        )

    opportunity = get_object_or_404(
        ProductOpportunity,
        id=opportunity_id,
    )

    if request.method != "POST":
        return redirect(
            "dashboard:home"
        )

    service = OpportunityReviewService()

    service.reject(
        opportunity
    )

    return redirect(
        "dashboard:home"
    )



