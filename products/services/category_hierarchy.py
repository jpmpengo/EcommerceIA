from django.db import transaction
from django.utils.text import slugify
from products.models import Category
from products.services.category_normalization import CategoryNormalizationService


class CategoryHierarchyService:
    @staticmethod
    def _ancestor_names(parent):
        names = []
        while parent is not None:
            names.insert(0, parent.name)
            parent = parent.parent
        return names

    @classmethod
    @transaction.atomic
    def create_approved_path(cls, category_path):
        path = [str(name).strip() for name in (category_path or []) if str(name).strip()]
        if len(path) != 3 or len(category_path or []) != 3:
            raise ValueError("La categorie doit comporter exactement trois niveaux non vides")
        parent = None
        for name in path:
            key = CategoryNormalizationService.normalize(name)
            canonical = CategoryNormalizationService.canonical_name(name)
            key = CategoryNormalizationService.normalize(canonical)
            category = next((item for item in Category.objects.filter(parent=parent) if CategoryNormalizationService.normalize(item.name) == key), None)
            if category is None:
                base_slug = slugify("-".join([*(cls._ancestor_names(parent)), canonical])) or "categorie"
                slug = base_slug
                suffix = 2
                while Category.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{suffix}"
                    suffix += 1
                category = Category.objects.create(parent=parent, name=canonical, slug=slug)
            parent = category
        return parent
