from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product_intelligence", "0032_supplieroffer_supplier_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplieroffer",
            name="shipping_method",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
