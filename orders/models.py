from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente de paiement"),
        ("paid", "Payée"),
        ("expired", "Expirée"),
        ("cancelled", "Annulée"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=30,
    )

    address = models.CharField(
        max_length=255,
    )

    postal_code = models.CharField(
        max_length=20,
    )

    city = models.CharField(
        max_length=100,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
    )

    # Conservé pour compatibilité avec
    # le code Stripe et les templates existants.
    paid = models.BooleanField(
        default=False,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    reservation_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Commande {self.id} - "
            f"{self.first_name} {self.last_name}"
        )

    def get_total_price(self):
        return sum(
            item.get_cost()
            for item in self.items.all()
        )

    def set_reservation_expiration(self):
        self.reservation_expires_at = (
            timezone.now()
            + timedelta(minutes=30)
        )

    def reservation_has_expired(self):
        if not self.reservation_expires_at:
            return False

        return (
            timezone.now()
            >= self.reservation_expires_at
        )


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
    )

    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.PROTECT,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    def __str__(self):
        return (
            f"{self.quantity} × "
            f"{self.product.name}"
        )

    def get_cost(self):
        return self.price * self.quantity