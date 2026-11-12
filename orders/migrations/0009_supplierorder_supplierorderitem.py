from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0008_supplierpreparation_profitability"),
        ("product_intelligence", "0033_supplieroffer_shipping_method"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupplierOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mode", models.CharField(choices=[("sandbox", "Sandbox"), ("production", "Production")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "À transmettre"), ("submitted", "Transmise"), ("failed", "Échec à vérifier")], default="pending", max_length=20)),
                ("idempotency_key", models.CharField(max_length=100, unique=True)),
                ("supplier_order_id", models.CharField(blank=True, max_length=255)),
                ("request_payload", models.JSONField(blank=True, default=dict)),
                ("response_payload", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="supplier_orders", to="orders.order")),
                ("supplier", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="supplier_orders", to="product_intelligence.supplier")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="SupplierOrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("supplier_line_id", models.CharField(blank=True, max_length=255)),
                ("order_item", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="supplier_order_item", to="orders.orderitem")),
                ("supplier_order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.supplierorder")),
                ("supplier_preparation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="submitted_items", to="orders.supplierpreparation")),
            ],
        ),
        migrations.AddConstraint(
            model_name="supplierorder",
            constraint=models.UniqueConstraint(fields=("order", "supplier", "mode"), name="unique_supplier_order_per_mode"),
        ),
    ]
