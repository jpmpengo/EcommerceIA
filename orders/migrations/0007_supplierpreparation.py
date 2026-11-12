from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0006_order_country"),
        ("product_intelligence", "0032_supplieroffer_supplier_identity"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupplierPreparation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mode", models.CharField(choices=[("simulation", "Simulation")], default="simulation", max_length=20)),
                ("destination_country", models.CharField(max_length=2)),
                ("quantity", models.PositiveIntegerField()),
                ("source_currency", models.CharField(max_length=3)),
                ("target_currency", models.CharField(default="EUR", max_length=3)),
                ("exchange_rate", models.DecimalField(decimal_places=6, max_digits=18)),
                ("purchase_original", models.DecimalField(decimal_places=2, max_digits=12)),
                ("shipping_original", models.DecimalField(decimal_places=2, max_digits=12)),
                ("purchase_converted", models.DecimalField(decimal_places=2, max_digits=12)),
                ("shipping_converted", models.DecimalField(decimal_places=2, max_digits=12)),
                ("base_cost", models.DecimalField(decimal_places=2, max_digits=12)),
                ("import_duty_rate", models.DecimalField(decimal_places=4, max_digits=6)),
                ("import_duty", models.DecimalField(decimal_places=2, max_digits=12)),
                ("landed_cost", models.DecimalField(decimal_places=2, max_digits=12)),
                ("rate_source", models.URLField(blank=True)),
                ("supplier_verified_at", models.DateTimeField()),
                ("calculated_at", models.DateTimeField()),
                ("order_item", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="supplier_preparation", to="orders.orderitem")),
                ("supplier_offer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="supplier_preparations", to="product_intelligence.supplieroffer")),
            ],
            options={"ordering": ["-calculated_at"]},
        ),
    ]
