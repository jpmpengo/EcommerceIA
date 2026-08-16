from django.urls import path

from . import views

app_name = "recommendations"

urlpatterns = [

    path(
        "",
        views.recommendation_list,
        name="list",
    ),

    path(
        "<int:pk>/",
        views.recommendation_detail,
        name="detail",
    ),
    path(
        "<int:pk>/publish/",
        views.publish_recommendation,
        name="publish",
    ),
    path(
        "<int:pk>/postpone/",
        views.postpone_recommendation,
        name="postpone",
    ),
    path(
        "<int:pk>/reject/",
        views.reject_recommendation,
        name="reject",
    ),
    path(
        "<int:pk>/apply-category/",
        views.apply_category,
        name="apply_category",
    ),
    path(
        "<int:pk>/apply-description/",
        views.apply_description,
        name="apply_description",
    ),
    path(
        "<int:pk>/apply-image/",
        views.apply_image,
        name="apply_image",
    ),
    path(
        "<int:pk>/apply-supplier-image/",
        views.apply_supplier_image,
        name="apply_supplier_image",
    ),
    path(
        "<int:pk>/apply-stock/",
        views.apply_stock,
        name="apply_stock",
    ),  
    path(
        "<int:pk>/restock/",
        views.restock_recommendation,
        name="restock",
    ),

]

