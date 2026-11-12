from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0009_supplierorder_supplierorderitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplierorder",
            name="supplier_status",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="supplierorder",
            name="supplier_sub_status",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="supplierorder",
            name="tracking_number",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="supplierorder",
            name="tracking_provider",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="supplierorder",
            name="tracking_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="supplierorder",
            name="last_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
