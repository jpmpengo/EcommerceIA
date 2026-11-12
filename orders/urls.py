from django.urls import path

from . import views


app_name = "orders"

urlpatterns = [
    path("satisfaction/<str:token>/", views.satisfaction_from_email, name="satisfaction_from_email"),
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
        "mes-commandes/<int:order_id>/satisfaction/",
        views.order_submit_satisfaction,
        name="order_submit_satisfaction",
    ),
    path(
        "mes-commandes/<int:order_id>/confirmer-reception/",
        views.order_confirm_receipt,
        name="order_confirm_receipt",
    ),
    path(
        "mes-commandes/<int:order_id>/signaler-livraison/",
        views.order_report_delivery_issue,
        name="order_report_delivery_issue",
    ),
    path(
        "mes-commandes/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),
    path(
        "mes-commandandes/".replace("commandandes","commandes") + chr(60) + "int:order_id" + chr(62) + "/facture/",
        views.invoice_detail,
        name="invoice_detail",
    ),
    path(
        "mes-commandes/" + chr(60) + "int:order_id" + chr(62) + "/facture/pdf/",
        views.invoice_pdf,
        name="invoice_pdf",
    ),
    path(
        "gestion-commandes/",
        views.operator_order_list,
        name="operator_order_list",
    ),
    path(
        "gestion-commandes/<int:order_id>/",
        views.operator_order_detail,
        name="operator_order_detail",
    ),
    path(
        "gestion-commandes/<int:order_id>/preparer-fournisseur/",
        views.operator_prepare_supplier_order,
        name="operator_prepare_supplier_order",
    ),
    path(
        "gestion-commandes/<int:order_id>/fournisseur/<int:supplier_order_id>/synchroniser/",
        views.operator_sync_supplier_order,
        name="operator_sync_supplier_order",
    ),
    path(
        "gestion-commandes/<int:order_id>/transmettre-fournisseur/",
        views.operator_submit_supplier_order,
        name="operator_submit_supplier_order",
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
