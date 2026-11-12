from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0005_sync_paid_order_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="country",
            field=models.CharField(
                blank=True,
                choices=[
                    ("FR", "France"),
                    ("BE", "Belgique"),
                    ("ES", "Espagne"),
                ],
                default="",
                max_length=2,
            ),
        ),
    ]
