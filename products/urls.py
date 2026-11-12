from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path('categories/retirer/<slug:slug>/', views.remove_category_selection, name='remove_category_selection'),
    path("categories/reinitialiser/", views.reset_category_selection, name="reset_category_selection"),
    path("", views.product_list, name="product_list"),
    path(
        "categorie/<slug:slug>/",
        views.products_by_category,
        name="products_by_category",
    ),
    path(
        "<int:product_id>/",
        views.product_detail,
        name="product_detail",
    ),
]
