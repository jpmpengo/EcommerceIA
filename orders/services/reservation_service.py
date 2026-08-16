from django.db.models import Sum
from django.utils import timezone

from orders.models import Order, OrderItem

from django.db import transaction
from products.models import Product

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from orders.models import OrderItem
from products.models import Product


class OrderReservationService:

    @staticmethod
    def get_available_stock(product):
        reserved_quantity = (
            OrderItem.objects
            .filter(
                product=product,
                order__status="pending",
                order__reservation_expires_at__gt=timezone.now(),
            )
            .aggregate(
                total=Sum("quantity")
            )
            ["total"]
            or 0
        )

        return max(
            product.stock - reserved_quantity,
            0,
        )

    @staticmethod
    @transaction.atomic
    def reserve(
        order,
        product,
        quantity,
    ):
        product = (
            Product.objects
            .select_for_update()
            .get(pk=product.pk)
        )

        available_stock = (
            OrderReservationService.get_available_stock(
                product
            )
        )

        if quantity <= 0:
            raise ValueError(
                "La quantité doit être supérieure à zéro."
            )

        if quantity > available_stock:
            raise ValueError(
                "Stock disponible insuffisant."
            )

        return OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=quantity,
        )

    @staticmethod
    def expire_order(order):
        if order.status != "pending":
            return order

        if not order.reservation_has_expired():
            return order

        order.status = "expired"

        order.save(
            update_fields=[
                "status",
            ]
        )

        return order

    @staticmethod
    def expire_pending_orders():
        expired_orders = (
            Order.objects.filter(
                status="pending",
                paid=False,
                reservation_expires_at__lte=timezone.now(),
            )
        )

        for order in expired_orders:
            OrderReservationService.expire_order(
                order
            )
