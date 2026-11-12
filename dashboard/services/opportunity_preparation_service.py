from django.db import transaction
from django.utils.text import slugify

from products.models import Category


class OpportunityPreparationService:

    @classmethod
    @transaction.atomic
    def update(
        cls,
        opportunity,
        name,
        description,
        category_id=None,
        initial_stock=None,
        new_category_name="",
    ):
        name = (name or "").strip()
        description = (description or "").strip()
        new_category_name = (
            new_category_name or ""
        ).strip()

        if not name:
            raise ValueError(
                "Le nom commercial est obligatoire."
            )

        if len(name) > 255:
            raise ValueError(
                "Le nom commercial est trop long."
            )

        if len(description) < 50:
            raise ValueError(
                "La description doit contenir au moins 50 caractères."
            )

        if initial_stock is not None:
            try:
                initial_stock = int(initial_stock)
            except (TypeError, ValueError):
                raise ValueError('Le stock initial doit être un nombre entier.')
            if initial_stock <= 0:
                raise ValueError('Le stock initial doit être supérieur à zéro.')
            available = getattr(opportunity.supplier_offer, 'stock', None)
            if available is not None and initial_stock > int(available):
                raise ValueError('Le stock initial dépasse le stock fournisseur disponible.')
        opportunity.name = name
        opportunity.description = description
        fields = ['name', 'description', 'updated_at']
        if initial_stock is not None:
            opportunity.initial_stock = initial_stock
            fields.append('initial_stock')
        opportunity.save(update_fields=fields)

        return opportunity

    @staticmethod
    def _get_or_create_category(name):
        existing = Category.objects.filter(
            name__iexact=name
        ).first()

        if existing is not None:
            return existing

        base_slug = slugify(name) or "categorie"
        slug = base_slug
        suffix = 2

        while Category.objects.filter(
            slug=slug
        ).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return Category.objects.create(
            name=name,
            slug=slug,
        )
