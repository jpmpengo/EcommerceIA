from functools import wraps

import httpx

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from dashboard.services.access_service import (
    DashboardAccessService,
)
from dashboard.services.business_advisor import (
    BusinessAdvisor,
)
from dashboard.services.category_assignment_service import (
    CategoryAssignmentService,
)
from dashboard.services.category_suggestion_service import (
    CategorySuggestionService,
)
from dashboard.services.description_suggestion_service import (
    DescriptionSuggestionService,
)
from dashboard.services.publication_readiness_service import (
    PublicationReadinessService,
)
from dashboard.services.stock_suggestion_service import (
    StockSuggestionService,
)

from product_intelligence.models import (
    ProductOpportunity,
)
from product_intelligence.services.advisor import (
    OpportunityAdvisor,
)
from product_intelligence.services.restock_service import (
    RestockService,
)

from recommendations.services.decision_service import (
    RecommendationDecisionService,
)
from recommendations.services.supplier_image_service import (
    SupplierImageService,
)

from django.views.decorators.http import (
    require_POST,
)

def emma_access_required(view_function):
    @wraps(view_function)
    @login_required
    def protected_view(
        request,
        *args,
        **kwargs,
    ):
        if not DashboardAccessService.can_access(
            request.user
        ):
            return redirect(
                "products:product_list"
            )

        return view_function(
            request,
            *args,
            **kwargs,
        )

    return protected_view

@emma_access_required
def recommendation_list(request):
    advisor = BusinessAdvisor()
    brief = advisor.get_business_brief()

    return render(
        request,
        "recommendations/list.html",
        {
            "recommendations": brief[
                "top_opportunities"
            ],
        },
    )

@emma_access_required
def recommendation_detail(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    recommendation = OpportunityAdvisor.get_recommendation(
        opportunity
    )

    readiness = PublicationReadinessService.evaluate(
        opportunity
    )

    stock_missing = any(
        item["field"] == "initial_stock"
        for item in readiness["missing"]
    )

    suggested_stock = None

    if stock_missing:
        suggested_stock = (
            StockSuggestionService.suggest(
                opportunity
            )
        )

    suggested_category = None

    if opportunity.category is None:
        suggested_category = (
            CategorySuggestionService.suggest(
                opportunity
            )
        )

    suggested_description = None

    if any(
        item["field"] == "description"
        for item in readiness["missing"]
    ):
        suggested_description = (
            DescriptionSuggestionService.suggest(
                opportunity
            )
        )

    image_missing = any(
        item["field"] == "image"
        for item in readiness["missing"]
    )

    suggested_image_url = None

    if (
        image_missing
        and opportunity.supplier_offer is not None
    ):
        suggested_image_url = (
            opportunity.supplier_offer.image_url
            or None
        )

    is_restock = (
        opportunity.restock_product is not None
    )

    restock_product = (
        opportunity.restock_product
        if is_restock
        else None
    )

    return render(
        request,
        "recommendations/detail.html",
        {
            "opportunity": opportunity,
            "recommendation": recommendation,
            "readiness": readiness,
            "suggested_category": suggested_category,
            "suggested_description": suggested_description,
            "image_missing": image_missing,
            "stock_missing": stock_missing,
            "suggested_stock": suggested_stock,
            "is_restock": is_restock,
            "restock_product": restock_product,
            "suggested_image_url": suggested_image_url,
        },
    )

@emma_access_required
@require_POST
def publish_recommendation(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    try:
        RecommendationDecisionService.publish(
            opportunity
        )

        messages.success(
            request,
            (
                f'🎉 "{opportunity.name}" '
                "a été publié avec succès."
            ),
        )

        return redirect(
            "dashboard:home"
        )

    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

@emma_access_required
@require_POST
def postpone_recommendation(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    try:
        RecommendationDecisionService.postpone(
            opportunity
        )

        messages.success(
            request,
            "La recommandation a été reportée pendant 14 jours.",
        )

    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

    return redirect(
        "recommendations:list"
    )


@emma_access_required
@require_POST
def reject_recommendation(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    try:
        RecommendationDecisionService.reject(
            opportunity
        )

        messages.success(
            request,
            "La recommandation a été rejetée.",
        )

    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

    return redirect(
        "recommendations:list"
    )

@emma_access_required
@require_POST
def apply_category(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    category = (
        CategorySuggestionService.suggest(
            opportunity
        )
    )

    if category is None:
        messages.error(
            request,
            "Emma n'a trouvé aucune catégorie adaptée.",
        )
    else:
        CategoryAssignmentService.assign(
            opportunity,
            category,
        )

        messages.success(
            request,
            (
                "✅ La catégorie "
                f'"{category.name}" '
                "a été appliquée."
            ),
        )

    return redirect(
        "recommendations:detail",
        pk=opportunity.pk,
    )

@emma_access_required
@require_POST
def apply_description(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    suggested_description = (
        DescriptionSuggestionService.suggest(
            opportunity
        )
    )

    if suggested_description is None:
        messages.error(
            request,
            "Emma n'a pas trouvé de description adaptée.",
        )
    else:
        opportunity.description = (
            suggested_description
        )

        opportunity.save(
            update_fields=[
                "description",
            ]
        )

        messages.success(
            request,
            "✅ La description proposée par Emma a été appliquée.",
        )

    return redirect(
        "recommendations:detail",
        pk=opportunity.pk,
    )

@emma_access_required
@require_POST
def apply_image(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    if request.method == "POST":
        image = request.FILES.get(
            "image"
        )

        if not image:
            messages.error(
                request,
                "Veuillez sélectionner une image.",
            )

            return redirect(
                "recommendations:detail",
                pk=opportunity.pk,
            )

        opportunity.image = image

        opportunity.save(
            update_fields=[
                "image",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "L'image du produit a été ajoutée.",
        )

    return redirect(
        "recommendations:detail",
        pk=opportunity.pk,
    )

@emma_access_required
@require_POST
def apply_supplier_image(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    if request.method != "POST":
        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

    if opportunity.supplier_offer is None:
        messages.error(
            request,
            (
                "Aucune offre fournisseur n'est liée "
                "à cette opportunité."
            ),
        )

        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

    image_url = (
        opportunity.supplier_offer.image_url
    )

    if not image_url:
        messages.error(
            request,
            "Aucune image fournisseur n'est disponible.",
        )

        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

    try:
        image_data = SupplierImageService.download(
            image_url
        )

        filename = (
            f"supplier_{opportunity.pk}"
            f"{image_data['extension']}"
        )

        opportunity.image.save(
            filename,
            ContentFile(
                image_data["content"]
            ),
            save=False,
        )

        opportunity.save(
            update_fields=[
                "image",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "✅ L'image fournisseur a été enregistrée.",
        )

    except (
        httpx.HTTPError,
        ValueError,
    ):
        messages.error(
            request,
            (
                "Impossible de télécharger "
                "l'image fournisseur."
            ),
        )

    return redirect(
        "recommendations:detail",
        pk=opportunity.pk,
    )

@emma_access_required
@require_POST
def apply_stock(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    if request.method != "POST":
        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

    stock_value = request.POST.get(
        "initial_stock"
    )

    try:
        stock_value = int(
            stock_value
        )
    except (TypeError, ValueError):
        stock_value = 0

    if stock_value <= 0:
        messages.error(
            request,
            "Le stock initial doit être supérieur à zéro.",
        )

        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

    opportunity.initial_stock = stock_value

    opportunity.save(
        update_fields=[
            "initial_stock",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            "✅ Le stock initial a été défini à "
            f"{stock_value} unité(s)."
        ),
    )

    return redirect(
        "recommendations:detail",
        pk=opportunity.pk,
    )

@emma_access_required
@require_POST
def restock_recommendation(request, pk):
    opportunity = get_object_or_404(
        ProductOpportunity,
        pk=pk,
    )

    if request.method != "POST":
        return redirect(
            "recommendations:detail",
            pk=opportunity.pk,
        )

    quantity = request.POST.get(
        "quantity"
    )

    try:
        quantity = int(
            quantity
        )
    except (TypeError, ValueError):
        quantity = 0

    try:
        product = RestockService.restock(
            opportunity=opportunity,
            quantity=quantity,
        )

        messages.success(
            request,
            (
                f'Le produit "{product.name}" '
                "a été réapprovisionné de "
                f"{quantity} unité(s)."
            ),
        )

        return redirect(
            "dashboard:home"
        )

    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

    return redirect(
        "recommendations:detail",
        pk=opportunity.pk,
    )

    
