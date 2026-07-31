from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "inscription/",
        views.register,
        name="register",
    ),
]
