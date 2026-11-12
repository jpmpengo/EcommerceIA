from django.contrib import admin

from .models import (
    Order,
    OrderItem,
    SupplierOrder,
    SupplierOrderItem,
    SupplierPreparation,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "first_name",
        "last_name",
        "email",
        "city",
        "country",
        "paid",
        "status",
        "created_at",
    ]

    list_filter = [
        "paid",
        "status",
        "created_at",
    ]

    search_fields = [
        "first_name",
        "last_name",
        "email",
    ]

    inlines = [OrderItemInline]


@admin.register(SupplierPreparation)
class SupplierPreparationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order_item",
        "supplier_offer",
        "mode",
        "destination_country",
        "import_duty_method",
        "landed_cost",
        "target_currency",
        "calculated_at",
    ]
    list_filter = ["mode", "destination_country", "calculated_at"]


class SupplierOrderItemInline(admin.TabularInline):
    model = SupplierOrderItem
    extra = 0
    readonly_fields = ["order_item", "supplier_preparation", "supplier_line_id"]


@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "supplier",
        "mode",
        "status",
        "supplier_order_id",
        "supplier_status",
        "tracking_number",
        "submitted_at",
    ]
    list_filter = ["mode", "status", "supplier"]
    readonly_fields = [
        "idempotency_key",
        "request_payload",
        "response_payload",
        "error_message",
        "submitted_at",
        "supplier_status",
        "supplier_sub_status",
        "tracking_number",
        "tracking_provider",
        "tracking_url",
        "last_synced_at",
    ]
    inlines = [SupplierOrderItemInline]

    
