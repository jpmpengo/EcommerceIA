from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Product
from .services.category_selection import category_union_filter, refine_selection
from .services.product_search_synonyms import build_search_groups


def _term_filter(term):
    return (
        Q(name__icontains=term)
        | Q(description__icontains=term)
        | Q(category__name__icontains=term)
    )


def _search_products(request, queryset):
    search_query = request.GET.get("q", "").strip()

    if not search_query:
        return queryset, ""

    # ET entre les intentions saisies, OU entre leurs synonymes.
    # Exemple : "souris sans fil" => (souris OU mouse) ET (sans fil OU wireless).
    for synonym_group in build_search_groups(search_query):
        group_filter = Q()
        for term in synonym_group:
            group_filter |= _term_filter(term)
        queryset = queryset.filter(group_filter)

    queryset = (
        queryset
        .annotate(
            search_rank=Case(
                When(name__icontains=search_query, then=Value(0)),
                When(category__name__icontains=search_query, then=Value(1)),
                When(description__icontains=search_query, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        )
        .order_by("search_rank", "name")
        .distinct()
    )

    return queryset, search_query


def _selected_categories(request, category=None):
    ids = request.session.get("catalog_category_ids", [])
    categories = list(Category.objects.filter(id__in=ids))
    valid_ids = [item.id for item in categories]
    if category is not None:
        valid_ids = refine_selection(valid_ids, category)
    if valid_ids != ids:
        request.session["catalog_category_ids"] = valid_ids
    return list(Category.objects.filter(id__in=valid_ids))


def remove_category_selection(request, slug):
    category = get_object_or_404(Category, slug=slug)
    ids = request.session.get("catalog_category_ids", [])
    request.session["catalog_category_ids"] = [item for item in ids if item != category.id]
    return redirect("products:product_list")


def reset_category_selection(request):
    request.session.pop("catalog_category_ids", None)
    return redirect("products:product_list")


def product_list(request):
    products = Product.objects.filter(
        is_available=True,
    ).select_related("category")

    selected_categories = _selected_categories(request)
    if selected_categories:
        products = products.filter(category_union_filter(selected_categories)).distinct()

    products, search_query = _search_products(request, products)

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "search_query": search_query,
            "selected_categories": selected_categories,
        },
    )


def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    return render(
        request,
        "products/product_detail.html",
        {"product": product},
    )


def products_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    selected_categories = _selected_categories(request, category)

    products = Product.objects.filter(
        is_available=True,
    ).select_related("category")
    products = products.filter(category_union_filter(selected_categories)).distinct()

    products, search_query = _search_products(request, products)

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "category": category,
            "selected_categories": selected_categories,
            "search_query": search_query,
        },
    )
