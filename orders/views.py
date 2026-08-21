from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import stripe

from cart.cart import Cart
from products.models import Product

from orders.services.payment_service import (
    OrderPaymentService,
)
from orders.services.reservation_service import (
    OrderReservationService,
)

from .forms import OrderCreateForm
from .models import Order


def _get_accessible_order(
    request,
    order_id,
):
    orders = Order.objects.prefetch_related(
        "items__product"
    )

    if request.user.is_authenticated:
        return get_object_or_404(
            orders,
            id=order_id,
            user=request.user,
        )

    guest_order_ids = request.session.get(
        "guest_order_ids",
        [],
    )

    if order_id not in guest_order_ids:
        raise Http404(
            "Cette commande n'est pas accessible."
        )

    return get_object_or_404(
        orders,
        id=order_id,
        user__isnull=True,
    )


def order_create(request):
    cart = Cart(request)

    if request.method == "POST":
        form = OrderCreateForm(
            request.POST
        )

        if form.is_valid():
            cart_items = list(cart)

            if not cart_items:
                messages.warning(
                    request,
                    "Votre panier est vide.",
                )

                return redirect(
                    "cart:cart_detail"
                )

            try:
                with transaction.atomic():
                    locked_products = {}

                    for item in cart_items:
                        product = (
                            Product.objects
                            .select_for_update()
                            .get(
                                id=(
                                    item["product"].id
                                )
                            )
                        )

                        locked_products[
                            product.id
                        ] = product

                        if (
                            not product.is_available
                            or item["quantity"]
                            > product.stock
                        ):
                            raise ValueError(
                                (
                                    f"Le produit « {product.name} » "
                                    "n'a plus assez de stock."
                                )
                            )

                    order = form.save(
                        commit=False
                    )

                    if request.user.is_authenticated:
                        order.user = (
                            request.user
                        )

                    order.save()

                    order.set_reservation_expiration()

                    order.save(
                        update_fields=[
                            "reservation_expires_at",
                        ]
                    )

                    for item in cart_items:
                        product = (
                            locked_products[
                                item["product"].id
                            ]
                        )

                        quantity = (
                            item["quantity"]
                        )

                        OrderReservationService.reserve(
                            order=order,
                            product=product,
                            quantity=quantity,
                        )

            except ValueError as exc:
                messages.error(
                    request,
                    str(exc),
                )

                return redirect(
                    "cart:cart_detail"
                )

            cart.clear()

            if not request.user.is_authenticated:
                guest_order_ids = (
                    request.session.get(
                        "guest_order_ids",
                        [],
                    )
                )

                if order.id not in guest_order_ids:
                    guest_order_ids.append(
                        order.id
                    )

                request.session[
                    "guest_order_ids"
                ] = guest_order_ids

                request.session.modified = True

            return redirect(
                "orders:order_created",
                order_id=order.id,
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

def order_created(
    request,
    order_id,
):
    order = _get_accessible_order(
        request,
        order_id,
    )

    order = (
        OrderReservationService
        .expire_order(
            order
        )
    )

    return render(
        request,
        "orders/order_created.html",
        {
            "order": order,
        },
    )

def payment_create(
    request,
    order_id,
):
    order = _get_accessible_order(
        request,
        order_id,
    )

    if order.paid:
        raise Http404(
            "Cette commande est déjà payée."
        )

    if order.reservation_has_expired():
        order.status = "expired"

        order.save(
            update_fields=[
                "status",
            ]
        )

        messages.error(
            request,
            (
                "La réservation de cette commande "
                "a expiré. Le paiement n'est plus "
                "disponible."
            ),
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    if order.status != "pending":
        messages.error(
            request,
            (
                "Cette commande ne peut plus "
                "être payée."
            ),
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    stripe.api_key = (
        settings.STRIPE_SECRET_KEY
    )

    line_items = []

    for item in order.items.all():
        line_items.append(
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": (
                            item.product.name
                        ),
                    },
                    "unit_amount": int(
                        item.price * 100
                    ),
                },
                "quantity": item.quantity,
            }
        )

    success_url = (
        request.build_absolute_uri(
            reverse(
                "orders:payment_success"
            )
        )
    )

    success_url += (
        "?session_id="
        "{CHECKOUT_SESSION_ID}"
    )

    cancel_url = (
        request.build_absolute_uri(
            reverse(
                "orders:order_detail",
                args=[
                    order.id,
                ],
            )
        )
    )

    checkout_session = (
        stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(
                order.id
            ),
            metadata={
                "order_id": str(
                    order.id
                ),
            },
        )
    )

    order.stripe_checkout_session_id = (
        checkout_session.id
    )

    order.save(
        update_fields=[
            "stripe_checkout_session_id",
        ]
    )

    return HttpResponse(
        status=303,
        headers={
            "Location": checkout_session.url,
        },
    )


def payment_success(request):
    session_id = request.GET.get(
        "session_id"
    )

    if not session_id:
        messages.error(
            request,
            (
                "La session de paiement "
                "est introuvable."
            ),
        )

        if request.user.is_authenticated:
            return redirect(
                "orders:order_list"
            )

        return redirect(
            "cart:cart_detail"
        )

    stripe.api_key = (
        settings.STRIPE_SECRET_KEY
    )

    checkout_session = (
        stripe.checkout.Session.retrieve(
            session_id
        )
    )

    metadata = getattr(
        checkout_session,
        "metadata",
        {},
    )

    order_id = getattr(
        metadata,
        "order_id",
        None,
    )

    if (
        order_id is None
        and isinstance(metadata, dict)
    ):
        order_id = metadata.get(
            "order_id"
        )

    if order_id is None:
        raise Http404(
            (
                "La commande associée "
                "est introuvable."
            )
        )

    try:
        order_id = int(
            order_id
        )
    except (
        TypeError,
        ValueError,
    ):
        raise Http404(
            (
                "L'identifiant de commande "
                "est invalide."
            )
        )

    order = _get_accessible_order(
        request,
        order_id,
    )

    if (
        order.stripe_checkout_session_id
        != session_id
    ):
        raise Http404(
            (
                "Cette session de paiement "
                "ne correspond pas à la commande."
            )
        )

    return render(
        request,
        "orders/payment_success.html",
        {
            "order": order,
            "checkout_session": (
                checkout_session
            ),
        },
    )

def order_list(request):
    orders = Order.objects.prefetch_related(
        "items__product"
    )

    if request.user.is_authenticated:
        orders = orders.filter(
            user=request.user,
        )

    else:
        guest_order_ids = request.session.get(
            "guest_order_ids",
            [],
        )

        orders = orders.filter(
            id__in=guest_order_ids,
            user__isnull=True,
        )

    (
        OrderReservationService
        .expire_overdue_orders(
            orders
        )
    )

    orders = orders.order_by(
        "-id"
    )

    return render(
        request,
        "orders/order_list.html",
        {
            "orders": orders,
        },
    )

def order_detail(
    request,
    order_id,
):
    order = _get_accessible_order(
        request,
        order_id,
    )

    order = (
        OrderReservationService
        .expire_order(
            order
        )
    )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
        },
    )

@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(
            status=405
        )

    payload = request.body

    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE"
    )

    try:
        event = (
            stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=(
                    settings
                    .STRIPE_WEBHOOK_SECRET
                ),
            )
        )

    except ValueError:
        return HttpResponse(
            status=400
        )

    except (
        stripe.error
        .SignatureVerificationError
    ):
        return HttpResponse(
            status=400
        )

    if (
        event["type"]
        == "checkout.session.completed"
    ):
        session = event[
            "data"
        ][
            "object"
        ]

        metadata = session.get(
            "metadata",
            {},
        )

        order_id = metadata.get(
            "order_id"
        )

        if order_id:
            order = (
                Order.objects
                .filter(
                    id=order_id,
                    paid=False,
                )
                .first()
            )

            if order is not None:
                (
                    OrderPaymentService
                    .confirm_payment(
                        order_id=order_id,
                        stripe_session_id=(
                            session["id"]
                        ),
                    )
                )

    return HttpResponse(
        status=200
    )

def order_cancel(
    request,
    order_id,
):
    order = _get_accessible_order(
        request,
        order_id,
    )

    if request.method != "POST":
        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    if (
        order.status == "pending"
        and not order.paid
    ):
        order.status = "cancelled"

        order.save(
            update_fields=[
                "status",
            ]
        )

        messages.success(
            request,
            (
                "Votre commande a été "
                "annulée."
            ),
        )

    return redirect(
        "orders:order_detail",
        order_id=order.id,
    )
