from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(is_available=True)

    return render(
        request,
        "products/product_list.html",
        {"products": products},
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

    products = Product.objects.filter(
        category=category,
        is_available=True,
    )

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "category": category,
        },
    )
