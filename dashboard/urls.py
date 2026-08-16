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

]