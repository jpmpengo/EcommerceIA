from django.urls import path

from . import views


app_name = "dashboard"

urlpatterns = [

    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "opportunity/<int:opportunity_id>/approve/",
        views.approve_opportunity,
        name="approve_opportunity",
    ),

    path(
        "opportunity/<int:opportunity_id>/reject/",
        views.reject_opportunity,
        name="reject_opportunity",
    ),

    path(
        "product-ideas/",
        views.product_idea_list,
        name="product_idea_list",
    ),

    path(
        "product-ideas/<int:idea_id>/select/",
        views.select_product_idea,
        name="select_product_idea",
    ),

    path(
        "product-ideas/<int:idea_id>/reject/",
        views.reject_product_idea,
        name="reject_product_idea",
    ),

    path(
        "product-ideas/<int:idea_id>/prepare-study/",
        views.prepare_marketplace_study,
        name="prepare_marketplace_study",
    ),

    path(
        "marketplace-studies/<int:study_id>/run/",
        views.run_marketplace_study,
        name="run_marketplace_study",
    ),

]