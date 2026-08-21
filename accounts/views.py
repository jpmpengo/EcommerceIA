from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import (
    redirect,
    render,
)

from orders.models import Order

from .forms import RegisterForm


def _get_latest_guest_order(
    request,
):
    guest_order_ids = (
        request.session.get(
            "guest_order_ids",
            [],
        )
    )

    if not guest_order_ids:
        return None

    return (
        Order.objects.filter(
            id__in=guest_order_ids,
            user__isnull=True,
        )
        .order_by("-id")
        .first()
    )


def register(request):
    if request.method == "POST":
        form = RegisterForm(
            request.POST
        )

        if form.is_valid():
            guest_order_ids = list(
                request.session.get(
                    "guest_order_ids",
                    [],
                )
            )

            with transaction.atomic():
                user = form.save()

                matching_orders = (
                    Order.objects.filter(
                        id__in=guest_order_ids,
                        user__isnull=True,
                        email__iexact=(
                            user.email
                        ),
                    )
                )

                linked_order_ids = list(
                    matching_orders.values_list(
                        "id",
                        flat=True,
                    )
                )

                matching_orders.update(
                    user=user
                )

            login(
                request,
                user,
            )

            remaining_order_ids = [
                order_id
                for order_id
                in guest_order_ids
                if order_id
                not in linked_order_ids
            ]

            if remaining_order_ids:
                request.session[
                    "guest_order_ids"
                ] = remaining_order_ids
            else:
                request.session.pop(
                    "guest_order_ids",
                    None,
                )

            return redirect(
                "orders:order_list"
            )

    else:
        guest_order = (
            _get_latest_guest_order(
                request
            )
        )

        initial = {}

        if guest_order:
            initial = {
                "email": (
                    guest_order.email
                ),
                "first_name": (
                    guest_order.first_name
                ),
                "last_name": (
                    guest_order.last_name
                ),
            }

        form = RegisterForm(
            initial=initial
        )

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )
