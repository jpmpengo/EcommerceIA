from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0007_supplierpreparation"),
    ]

    operations = [
        migrations.AddField(model_name="supplierpreparation", name="sale_ttc", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="vat_rate", field=models.DecimalField(decimal_places=4, default=0, max_digits=6)),
        migrations.AddField(model_name="supplierpreparation", name="vat_amount", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="net_revenue", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="payment_fee", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="return_reserve", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="safety_reserve", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="total_costs", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="projected_profit", field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name="supplierpreparation", name="projected_margin_rate", field=models.DecimalField(decimal_places=2, default=0, max_digits=7)),
    ]
