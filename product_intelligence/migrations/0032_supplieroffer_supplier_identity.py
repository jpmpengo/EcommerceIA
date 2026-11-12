from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product_intelligence", "0031_comparableprice_qualification_reason_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplieroffer",
            name="supplier_parent_product_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="supplieroffer",
            name="supplier_sku",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="supplieroffer",
            name="supplier_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
