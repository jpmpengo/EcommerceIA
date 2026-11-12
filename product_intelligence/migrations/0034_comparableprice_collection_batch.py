import uuid
from datetime import timedelta

from django.db import migrations, models


def group_existing_collections(apps, schema_editor):
    ComparablePrice = apps.get_model(
        "product_intelligence",
        "ComparablePrice",
    )

    offer_ids = (
        ComparablePrice.objects
        .values_list("supplier_offer_id", flat=True)
        .distinct()
    )

    for offer_id in offer_ids:
        prices = list(
            ComparablePrice.objects
            .filter(supplier_offer_id=offer_id)
            .order_by("observed_at", "id")
        )
        batches = []
        current_batch = []
        previous_time = None

        for price in prices:
            if (
                previous_time is not None
                and price.observed_at - previous_time
                > timedelta(minutes=5)
            ):
                batches.append(current_batch)
                current_batch = []
            current_batch.append(price)
            previous_time = price.observed_at

        if current_batch:
            batches.append(current_batch)

        for index, batch in enumerate(batches):
            batch_id = uuid.uuid4()
            is_current = index == len(batches) - 1
            ComparablePrice.objects.filter(
                id__in=[price.id for price in batch]
            ).update(
                collection_batch_id=batch_id,
                is_current=is_current,
            )


class Migration(migrations.Migration):

    dependencies = [
        (
            "product_intelligence",
            "0033_supplieroffer_shipping_method",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="comparableprice",
            name="collection_batch_id",
            field=models.UUIDField(
                blank=True,
                db_index=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="comparableprice",
            name="is_current",
            field=models.BooleanField(
                db_index=True,
                default=True,
            ),
        ),
        migrations.RunPython(
            group_existing_collections,
            migrations.RunPython.noop,
        ),
    ]
