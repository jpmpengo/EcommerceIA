from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from products.models import Product

from .forms import OrderCreateForm
from .models import OrderItem, Order

import stripe

from django.conf import settings
from django.urls import reverse

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt




def order_create(request):
    cart = Cart(request)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            cart_items = list(cart)

            if not cart_items:
                messages.warning(
                    request,
                    "Votre panier est vide.",
                )
                return redirect("cart:cart_detail")

            with transaction.atomic():
                locked_products = {}

                # Vérification du stock avant de créer la commande
                for item in cart_items:
                    product = Product.objects.select_for_update().get(
                        id=item["product"].id
                    )

                    locked_products[product.id] = product

                    if (
                        not product.is_available
                        or item["quantity"] > product.stock
                    ):
                        messages.error(
                            request,
                            (
                                f"Le produit « {product.name} » "
                                "n'a plus assez de stock."
                            ),
                        )
                        return redirect("cart:cart_detail")

                # Le stock est suffisant : création de la commande
                order = form.save(commit=False)

                if request.user.is_authenticated:
                    order.user = request.user

                order.save()

                # Création des lignes et diminution du stock
                for item in cart_items:
                    product = locked_products[item["product"].id]
                    quantity = item["quantity"]

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=item["price"],
                        quantity=quantity,
                    )

                    product.stock -= quantity
                    product.is_available = product.stock > 0

                    product.save(
                        update_fields=[
                            "stock",
                            "is_available",
                        ]
                    )

            cart.clear()

            return render(
                request,
                "orders/order_created.html",
                {"order": order},
            )

    else:
        form = OrderCreateForm()

    return render(
        request,
        "orders/order_create.html",
        {
            "cart": cart,
            "form": form,
        },
    )


@login_required
def payment_create(request, order_id):
    order = get_object_or_404(
        request.user.orders.prefetch_related("items__product"),
        id=order_id,
        paid=False,
    )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    line_items = []

    for item in order.items.all():
        line_items.append(
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": item.product.name,
                    },
                    "unit_amount": int(item.price * 100),
                },
                "quantity": item.quantity,
            }
        )

    success_url = request.build_absolute_uri(
        reverse("orders:payment_success")
    )

    success_url += "?session_id={CHECKOUT_SESSION_ID}"

    cancel_url = request.build_absolute_uri(
        reverse(
            "orders:order_detail",
            args=[order.id],
        )
    )

    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(order.id),
        metadata={
            "order_id": str(order.id),
        },
    )

    order.stripe_checkout_session_id = checkout_session.id
    order.save(
        update_fields=["stripe_checkout_session_id"]
    )

    return redirect(
        checkout_session.url,
        code=303,
    )


@login_required
def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        messages.error(
            request,
            "La session de paiement est introuvable.",
        )
        return redirect("orders:order_list")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.retrieve(
        session_id
    )

    order = get_object_or_404(
        request.user.orders,
        id=checkout_session.metadata.order_id,
    )

    return render(
        request,
        "orders/payment_success.html",
        {
            "order": order,
            "checkout_session": checkout_session,
        },
    )


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related(
        "items__product"
    )

    return render(
        request,
        "orders/order_list.html",
        {"orders": orders},
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        request.user.orders.prefetch_related("items__product"),
        id=order_id,
    )

    return render(
        request,
        "orders/order_detail.html",
        {"order": order},
    )
    
@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        metadata = session["metadata"]
        order_id = (
            metadata["order_id"]
            if "order_id" in metadata
            else None
        )

        if order_id:
            order = Order.objects.filter(
                id=order_id,
                paid=False,
            ).first()

            if order:
                order.paid = True
                order.stripe_checkout_session_id = session["id"]

                order.save(
                    update_fields=[
                        "paid",
                        "stripe_checkout_session_id",
                    ]
                )

                print(
                    f"Commande {order.id} marquée comme payée."
                )

    return HttpResponse(status=200)
    
