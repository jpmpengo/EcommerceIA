from django.shortcuts import get_object_or_404, render

from dashboard.services.business_advisor import BusinessAdvisor
from product_intelligence.models import ProductOpportunity
from product_intelligence.services.advisor import OpportunityAdvisor


def recommendation_list(request):
    advisor = BusinessAdvisor()
    brief = advisor.get_business_brief()

    return render(
        request,
        "recommendations/list.html",
        {
            "recommendations": brief["top_opportunities"],
        },
    )


def recommendation_detail(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    recommendation = OpportunityAdvisor.get_recommendation(
        opportunity
    )

    return render(
        request,
        "recommendations/detail.html",
        {
            "opportunity": opportunity,
            "recommendation": recommendation,
        },
    )
    