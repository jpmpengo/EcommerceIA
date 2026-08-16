from django.db import transaction

from orders.models import Order
from products.models import Product


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

        # Important :
        # Stripe peut envoyer plusieurs fois le même événement.
        # Une commande déjà payée ne doit jamais retirer
        # le stock une deuxième fois.
        if order.paid:
            return order

        for item in order.items.all():
            product = Product.objects.select_for_update().get(
                id=item.product_id
            )

            if item.quantity > product.stock:
                raise ValueError(
                    (
                        f"Stock insuffisant pour "
                        f"« {product.name} »."
                    )
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
            order.stripe_checkout_session_id = (
                stripe_session_id
            )

        order.save(
            update_fields=[
                "paid",
                "status",
                "stripe_checkout_session_id",
            ]
        )

        return order

        