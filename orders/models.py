from django.db import models

from products.models import Product
from django.conf import settings



class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
    )
    
    paid = models.BooleanField(default=False)


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande {self.id} - {self.first_name} {self.last_name}"

    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())


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
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    def get_cost(self):
        return self.price * self.quantity
        
