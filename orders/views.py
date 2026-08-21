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

import secrets

from datetime import timedelta

from django.contrib.auth.hashers import (
    make_password,
)
from django.core.mail import send_mail
from django.core.validators import (
    validate_email,
)
from django.core.exceptions import (
    ValidationError,
)
from django.utils import timezone

from django.contrib.auth.hashers import (
    check_password,
)

from django.utils.dateparse import (
    parse_datetime,
)


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

def order_recovery(request):
    if request.method == "POST":
        email = (
            request.POST
            .get("email", "")
            .strip()
            .lower()
        )

        try:
            validate_email(email)
        except ValidationError:
            return render(
                request,
                "orders/order_recovery.html",
                {
                    "email": email,
                    "error": (
                        "Saisissez une adresse "
                        "e-mail valide."
                    ),
                },
                status=400,
            )

        code = (
            f"{secrets.randbelow(1000000):06d}"
        )

        request.session[
            "order_recovery"
        ] = {
            "email": email,
            "code_hash": make_password(
                code
            ),
            "expires_at": (
                timezone.now()
                + timedelta(minutes=10)
            ).isoformat(),
            "attempts": 0,
        }

        order_exists = (
            Order.objects.filter(
                email__iexact=email,
            )
            .exists()
        )

        if order_exists:
            send_mail(
                subject=(
                    "Votre code EcommerceIA"
                ),
                message=(
                    "Votre code pour retrouver "
                    "vos commandes est : "
                    f"{code}\n\n"
                    "Ce code est valable "
                    "pendant 10 minutes."
                ),
                from_email=(
                    settings.DEFAULT_FROM_EMAIL
                ),
                recipient_list=[
                    email,
                ],
            )

        return redirect(
            "orders:order_recovery_verify"
        )

    return render(
        request,
        "orders/order_recovery.html",
    )

def order_recovery_verify(request):
    recovery = request.session.get(
        "order_recovery"
    )

    if not recovery:
        return redirect(
            "orders:order_recovery"
        )

    email = recovery.get(
        "email",
        "",
    )

    if request.method == "POST":
        code = (
            request.POST
            .get("code", "")
            .strip()
        )

        expires_at = parse_datetime(
            recovery.get(
                "expires_at",
                "",
            )
        )

        code_has_expired = (
            expires_at is None
            or timezone.now() >= expires_at
        )

        if code_has_expired:
            request.session.pop(
                "order_recovery",
                None,
            )

            messages.error(
                request,
                (
                    "Ce code a expiré. "
                    "Demandez un nouveau code."
                ),
            )

            return redirect(
                "orders:order_recovery"
            )

        attempts = int(
            recovery.get(
                "attempts",
                0,
            )
        )

        code_is_valid = (
            len(code) == 6
            and code.isdigit()
            and check_password(
                code,
                recovery.get(
                    "code_hash",
                    "",
                ),
            )
        )

        if not code_is_valid:
            attempts += 1

            if attempts >= 5:
                request.session.pop(
                    "order_recovery",
                    None,
                )

                messages.error(
                    request,
                    (
                        "Trop de tentatives. "
                        "Demandez un nouveau code."
                    ),
                )

                return redirect(
                    "orders:order_recovery"
                )

            recovery["attempts"] = attempts

            request.session[
                "order_recovery"
            ] = recovery

            return render(
                request,
                (
                    "orders/"
                    "order_recovery_verify.html"
                ),
                {
                    "email": email,
                    "error": (
                        "Le code saisi est incorrect."
                    ),
                },
                status=400,
            )

        recovered_order_ids = list(
            Order.objects.filter(
                email__iexact=email,
                user__isnull=True,
            )
            .values_list(
                "id",
                flat=True,
            )
        )

        existing_order_ids = set(
            request.session.get(
                "guest_order_ids",
                [],
            )
        )

        existing_order_ids.update(
            recovered_order_ids
        )

        request.session[
            "guest_order_ids"
        ] = list(
            existing_order_ids
        )

        request.session.pop(
            "order_recovery",
            None,
        )

        return redirect(
            "orders:order_list"
        )

    return render(
        request,
        "orders/order_recovery_verify.html",
        {
            "email": email,
        },
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
            customer_email=order.email,
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(
                order.id
            ),
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

    payment_status = getattr(
        checkout_session,
        "payment_status",
        None,
    )

    if payment_status != "paid":
        messages.warning(
            request,
            (
                "Le paiement n'est pas encore "
                "confirmé par Stripe."
            ),
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    order = (
        OrderPaymentService
        .confirm_payment(
            order_id=order.id,
            stripe_session_id=session_id,
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
