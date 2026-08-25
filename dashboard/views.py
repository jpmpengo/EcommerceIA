from .services.assistant import DailyAssistant

from dashboard.services.emma_briefing_service import (
    EmmaBriefingService,
)

from django.contrib.auth.decorators import login_required

from dashboard.services.business_advisor import BusinessAdvisor

from django.shortcuts import render, redirect

from django.shortcuts import get_object_or_404

from product_intelligence.models import (
    ProductIdea,
    ProductOpportunity,
)
from product_intelligence.services.opportunity_review import (
    OpportunityReviewService,
)

from dashboard.services.access_service import (
    DashboardAccessService,
)
from django.views.decorators.http import (
    require_POST,
)

from product_intelligence.services.product_idea_selection import (
    ProductIdeaSelectionService,
)
from django.contrib import messages

from product_intelligence.services.product_idea_generation import (
    ProductIdeaGenerationService,
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

    service.reject(
        opportunity
    )

    return redirect(
        "dashboard:home"
    )

@login_required
def product_idea_list(request):
    if not DashboardAccessService.can_access(
        request.user
    ):
        return redirect(
            "products:product_list"
        )

    product_ideas = (
        ProductIdea.objects
        .filter(
            status="proposed"
        )
        .order_by(
            "-created_at"
        )
    )

    selected_ideas = (
        ProductIdea.objects
        .filter(
            status="selected"
        )
        .order_by(
            "-updated_at"
        )
    )

    return render(
        request,
        "dashboard/product_idea_list.html",
        {
            "product_ideas": product_ideas,
            "selected_ideas": selected_ideas,
        },
    )

@login_required
@require_POST
def select_product_idea(
    request,
    idea_id,
):
    if not DashboardAccessService.can_access(
        request.user
    ):
        return redirect(
            "products:product_list"
        )

    idea = get_object_or_404(
        ProductIdea,
        pk=idea_id,
    )

    try:
        ProductIdeaSelectionService.select(
            idea
        )
    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

    return redirect(
        "dashboard:product_idea_list"
    )

@login_required
@require_POST
def reject_product_idea(
    request,
    idea_id,
):
    if not DashboardAccessService.can_access(
        request.user
    ):
        return redirect(
            "products:product_list"
        )

    idea = get_object_or_404(
        ProductIdea,
        pk=idea_id,
    )

    try:
        ProductIdeaSelectionService.reject(
            idea
        )
    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

    return redirect(
        "dashboard:product_idea_list"
    )

@login_required
@require_POST
def generate_product_ideas(
    request,
):
    if not DashboardAccessService.can_access(
        request.user
    ):
        return redirect(
            "products:product_list"
        )

    try:
        generated_count = (
            ProductIdeaGenerationService
            .generate()
        )
    except ValueError as error:
        messages.error(
            request,
            str(error),
        )
    except Exception:
        messages.error(
            request,
            (
                "Emma n’a pas pu générer "
                "de nouvelles idées."
            ),
        )
    else:
        messages.success(
            request,
            (
                f"{generated_count} nouvelle(s) "
                "idée(s) proposée(s) par Emma."
            ),
        )

    return redirect(
        "dashboard:product_idea_list"
    )