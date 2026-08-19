from django.db import migrations

PRODUCT_CATEGORIES = (
    (
        "Maison & Cuisine",
        "maison-cuisine",
    ),
    (
        "Mode & Accessoires",
        "mode-accessoires",
    ),
)


def seed_product_categories(
    apps,
    schema_editor,
):
    Category = apps.get_model(
        "products",
        "Category",
    )

    for name, slug in PRODUCT_CATEGORIES:
        category = (
            Category.objects
            .filter(
                name__iexact=name,
            )
            .first()
        )

        if category is None:
            Category.objects.create(
                name=name,
                slug=slug,
            )


class Migration(migrations.Migration):

    dependencies = [
        (
            "products",
            "0005_product_stock",
        ),
    ]

    operations = [
        migrations.RunPython(
            seed_product_categories,
            migrations.RunPython.noop,
        ),
    ]
