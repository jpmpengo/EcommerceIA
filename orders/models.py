from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


class Order(models.Model):

    COUNTRY_CHOICES = [
        ("FR", "France"),
        ("BE", "Belgique"),
        ("ES", "Espagne"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente de paiement"),
        ("paid", "Payée"),
        ("processing", "En préparation"),
        ("shipped", "Expédiée"),
        ("delivered", "Livrée"),
        ("expired", "Expirée"),
        ("cancelled", "Annulée"),
        ("refunded", "Remboursée"),
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

    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        blank=True,
        default="",
    )

    billing_same_as_shipping = models.BooleanField(
        default=True,
    )

    billing_first_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    billing_last_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    billing_address = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    billing_postal_code = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )

    billing_city = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    billing_country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        blank=True,
        default="",
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

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    customer_received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reception_assumed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reception_disputed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reception_request_claimed_at = models.DateTimeField(null=True, blank=True)
    reception_request_sent_at = models.DateTimeField(
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


class CustomerSatisfaction(models.Model):
    order = models.OneToOneField("Order", on_delete=models.CASCADE, related_name="satisfaction")
    request_claimed_at = models.DateTimeField(null=True, blank=True)
    request_sent_at = models.DateTimeField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, default="")
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Satisfaction commande {self.order_id}"


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


class SupplierPreparation(models.Model):
    MODE_CHOICES = [
        ("simulation", "Simulation"),
    ]

    order_item = models.OneToOneField(
        OrderItem,
        related_name="supplier_preparation",
        on_delete=models.CASCADE,
    )
    supplier_offer = models.ForeignKey(
        "product_intelligence.SupplierOffer",
        related_name="supplier_preparations",
        on_delete=models.PROTECT,
    )
    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default="simulation",
    )
    destination_country = models.CharField(max_length=2)
    quantity = models.PositiveIntegerField()
    source_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3, default="EUR")
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6)
    purchase_original = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_original = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_converted = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_converted = models.DecimalField(max_digits=12, decimal_places=2)
    base_cost = models.DecimalField(max_digits=12, decimal_places=2)
    import_duty_rate = models.DecimalField(max_digits=6, decimal_places=4)
    import_duty = models.DecimalField(max_digits=12, decimal_places=2)
    import_duty_method = models.CharField(max_length=40, blank=True)
    import_duty_unit_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    import_duty_rule_date = models.DateField(null=True, blank=True)
    customs_rule_source = models.URLField(blank=True)
    customs_clearance_fee = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    ioss_status = models.CharField(max_length=20, default="unverified")
    landed_cost = models.DecimalField(max_digits=12, decimal_places=2)
    sale_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    return_reserve = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    safety_reserve = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    projected_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    projected_margin_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    rate_source = models.URLField(blank=True)
    supplier_verified_at = models.DateTimeField()
    calculated_at = models.DateTimeField()

    class Meta:
        ordering = ["-calculated_at"]

    def __str__(self):
        return f"Préparation fournisseur commande #{self.order_item.order_id}"


class SupplierOrder(models.Model):
    MODE_CHOICES = [
        ("sandbox", "Sandbox"),
        ("production", "Production"),
    ]
    STATUS_CHOICES = [
        ("pending", "À transmettre"),
        ("submitted", "Transmise"),
        ("failed", "Échec à vérifier"),
    ]

    order = models.ForeignKey(
        Order,
        related_name="supplier_orders",
        on_delete=models.PROTECT,
    )
    supplier = models.ForeignKey(
        "product_intelligence.Supplier",
        related_name="supplier_orders",
        on_delete=models.PROTECT,
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    idempotency_key = models.CharField(max_length=100, unique=True)
    supplier_order_id = models.CharField(max_length=255, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    supplier_status = models.CharField(max_length=50, blank=True)
    supplier_sub_status = models.CharField(max_length=50, blank=True)
    tracking_number = models.CharField(max_length=200, blank=True)
    tracking_provider = models.CharField(max_length=200, blank=True)
    tracking_url = models.URLField(max_length=500, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    next_check_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["status", "mode", "next_check_at"], name="supplier_monitor_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "supplier", "mode"],
                name="unique_supplier_order_per_mode",
            ),
        ]

    def __str__(self):
        return f"Commande fournisseur {self.supplier} / #{self.order_id}"


class SupplierOrderItem(models.Model):
    supplier_order = models.ForeignKey(
        SupplierOrder,
        related_name="items",
        on_delete=models.CASCADE,
    )
    order_item = models.OneToOneField(
        OrderItem,
        related_name="supplier_order_item",
        on_delete=models.PROTECT,
    )
    supplier_preparation = models.ForeignKey(
        SupplierPreparation,
        related_name="submitted_items",
        on_delete=models.PROTECT,
    )
    supplier_line_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.order_item} via {self.supplier_order.supplier}"


class OrderProcessingEvent(models.Model):
    SOURCE_CHOICES = [
        ("automatic", "Automatique"),
        ("manual", "Manuel"),
        ("system", "Système"),
    ]

    order = models.ForeignKey(
        Order,
        related_name="processing_events",
        on_delete=models.CASCADE,
    )
    supplier_order = models.ForeignKey(
        SupplierOrder,
        related_name="processing_events",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=100)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["supplier_order"],
                condition=models.Q(event_type="supplier_payment_attempted"),
                name="unique_supplier_payment_attempt",
            ),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.event_type}"


class MerchantLegalEntity(models.Model):
    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255, blank=True)
    siren = models.CharField(max_length=9, blank=True)
    siret = models.CharField(max_length=14, blank=True)
    vat_number = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, default="FR")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["legal_name", "id"]
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=["is_active"],
                name="unique_active_merchant_legal_entity",
            ),
        ]

    @classmethod
    def get_active(cls):
        return cls.objects.get(is_active=True)

    def __str__(self):
        return self.trade_name or self.legal_name


class Invoice(models.Model):
    order = models.OneToOneField(
        Order,
        related_name="invoice",
        on_delete=models.PROTECT,
    )
    merchant = models.ForeignKey(
        MerchantLegalEntity,
        related_name="invoices",
        on_delete=models.PROTECT,
    )
    number = models.CharField(max_length=50, unique=True)

    merchant_legal_name = models.CharField(max_length=255, blank=True)
    merchant_trade_name = models.CharField(max_length=255, blank=True)
    merchant_siren = models.CharField(max_length=9, blank=True)
    merchant_siret = models.CharField(max_length=14, blank=True)
    merchant_vat_number = models.CharField(max_length=32, blank=True)
    merchant_address = models.CharField(max_length=255, blank=True)
    merchant_postal_code = models.CharField(max_length=20, blank=True)
    merchant_city = models.CharField(max_length=100, blank=True)
    merchant_country = models.CharField(max_length=2, blank=True)

    billing_first_name = models.CharField(max_length=100, blank=True)
    billing_last_name = models.CharField(max_length=100, blank=True)
    billing_address = models.CharField(max_length=255, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_country = models.CharField(max_length=2, blank=True)

    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at", "-id"]

    def __str__(self):
        return self.number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="invoice_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=255)
    image_url = models.CharField(max_length=500, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price_ttc = models.DecimalField(max_digits=12, decimal_places=2)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} x {self.description}"
