from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0010_supplierorder_tracking_status")]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente de paiement"),
                    ("paid", "Payée"),
                    ("processing", "En préparation"),
                    ("shipped", "Expédiée"),
                    ("delivered", "Livrée"),
                    ("expired", "Expirée"),
                    ("cancelled", "Annulée"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
