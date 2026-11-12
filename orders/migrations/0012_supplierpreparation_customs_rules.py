from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0011_alter_order_status")]

    operations = [
        migrations.AddField(
            model_name="supplierpreparation",
            name="import_duty_method",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="supplierpreparation",
            name="import_duty_unit_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="supplierpreparation",
            name="import_duty_rule_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="supplierpreparation",
            name="customs_rule_source",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="supplierpreparation",
            name="customs_clearance_fee",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="supplierpreparation",
            name="ioss_status",
            field=models.CharField(default="unverified", max_length=20),
        ),
    ]
