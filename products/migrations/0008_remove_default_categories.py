from django.db import migrations


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    Product = apps.get_model("products", "Product")
    db = schema_editor.connection.alias
    for slug in ("maison-cuisine", "mode-accessoires"):
        for category in Category.objects.using(db).filter(slug=slug):
            has_products = Product.objects.using(db).filter(category_id=category.pk).exists()
            has_children = Category.objects.using(db).filter(parent_id=category.pk).exists()
            if not has_products and not has_children:
                category.delete(using=db)


class Migration(migrations.Migration):
    dependencies = [("products", "0007_category_parent")]
    operations = [migrations.RunPython(remove_default_categories, migrations.RunPython.noop)]
