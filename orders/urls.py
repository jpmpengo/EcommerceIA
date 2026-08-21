from django.urls import path

from . import views


app_name = "orders"

urlpatterns = [
    path(
        "retrouver/",
        views.order_recovery,
        name="order_recovery",
    ),
    path(
        "retrouver/code/",
        views.order_recovery_verify,
        name="order_recovery_verify",
    ),
    path(
        "creer/",
        views.order_create,
        name="order_create",
    ),
    path(
        "confirmation/<int:order_id>/",
        views.order_created,
        name="order_created",
    ),
    path(
        "mes-commandes/",
        views.order_list,
        name="order_list",
    ),
    path(
        "mes-commandes/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),
    path(
        "paiement/<int:order_id>/",
        views.payment_create,
        name="payment_create",
    ),
    path(
        "paiement/succes/",
        views.payment_success,
        name="payment_success",
    ),
    path(
        "stripe/webhook/",
        views.stripe_webhook,
        name="stripe_webhook",
    ),
    path(
        "mes-commandes/<int:order_id>/annuler/",
        views.order_cancel,
        name="order_cancel",
    ),
]
