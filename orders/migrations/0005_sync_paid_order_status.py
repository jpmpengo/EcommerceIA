from django.db import migrations


def sync_paid_order_status(apps, schema_editor):
    Order = apps.get_model("orders", "Order")

    Order.objects.filter(
        paid=True,
        status="pending",
    ).update(
        status="paid",
    )


def reverse_sync_paid_order_status(apps, schema_editor):
    # On ne revient volontairement pas en arrière :
    # paid=True indique historiquement qu'un paiement
    # a réellement été effectué.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_order_reservation_expires_at_order_status"),
    ]

    operations = [
        migrations.RunPython(
            sync_paid_order_status,
            reverse_sync_paid_order_status,
        ),
    ]

    