from django.db import transaction

from orders.models import Order, OrderProcessingEvent
from products.models import Product

from .invoice_service import InvoiceService


class OrderPaymentService:

    @staticmethod
    @transaction.atomic
    def confirm_payment(order_id, stripe_session_id=None):
        order = (
            Order.objects
            .select_for_update()
            .prefetch_related("items__product")
            .get(id=order_id)
        )

        # Stripe peut envoyer plusieurs fois le meme evenement.
        # Une commande deja payee ne doit jamais retirer
        # le stock une deuxieme fois.
        if order.paid:
            InvoiceService.create_for_paid_order(order)
            return order

        for item in order.items.all():
            product = Product.objects.select_for_update().get(
                id=item.product_id
            )

            if item.quantity > product.stock:
                raise ValueError(
                    f"Stock insuffisant pour {product.name}."
                )

            product.stock -= item.quantity
            product.is_available = product.stock > 0
            product.save(
                update_fields=[
                    "stock",
                    "is_available",
                ]
            )

        order.paid = True
        order.status = "paid"

        if stripe_session_id:
            order.stripe_checkout_session_id = stripe_session_id

        order.save(
            update_fields=[
                "paid",
                "status",
                "stripe_checkout_session_id",
            ]
        )

        OrderProcessingEvent.objects.create(
            order=order,
            event_type="customer_payment_received",
            source="automatic",
        )
        InvoiceService.create_for_paid_order(order)

        return order
