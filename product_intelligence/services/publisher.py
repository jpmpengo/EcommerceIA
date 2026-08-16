"""
OpportunityPublisher

Responsabilité
--------------
Transformer une opportunité approuvée en produit.

Ce service :
- vérifie les prérequis ;
- crée le produit ;
- associe le produit à l'opportunité ;
- met à jour le statut.

Ce service ne :
- ne décide jamais si une opportunité doit être publiée ;
- ne présente jamais la décision à l'utilisateur.

Utilisé par
-----------
- RecommendationDecisionService
- Django Admin

Dépend de
---------
- Product
- ProductOpportunity
"""

from django.db import transaction

from products.models import Product

from django.core.files.base import ContentFile


class OpportunityPublisher:
    @staticmethod
    @transaction.atomic
    def publish(opportunity):
        if opportunity.published_product:
            raise ValueError(
                "Cette opportunité est déjà publiée."
            )

        if opportunity.status != "approved":
            raise ValueError(
                "Cette opportunité doit être approuvée."
            )

        recommended_price = opportunity.get_recommended_price()

        missing_fields = []

        if not opportunity.description:
            missing_fields.append("description")

        if not opportunity.category:
            missing_fields.append("catégorie")

        if not opportunity.image:
            missing_fields.append("image")

        if opportunity.initial_stock <= 0:
            missing_fields.append("stock initial")

        if recommended_price <= 0:
            missing_fields.append("prix conseillé")

        if missing_fields:
            raise ValueError(
                "Informations manquantes : "
                + ", ".join(missing_fields)
                + "."
            )

        original_image_name = opportunity.image.name

        opportunity.image.open("rb")

        image_content = opportunity.image.read()

        opportunity.image.close()

        product = Product.objects.create(
            category=opportunity.category,
            name=opportunity.name,
            description=opportunity.description,
            price=recommended_price,
            stock=opportunity.initial_stock,
            is_available=True,
        )

        product.image.save(
            original_image_name.split("/")[-1],
            ContentFile(image_content),
            save=True,
        )

        opportunity.published_product = product
        opportunity.status = "published"

        opportunity.image.delete(
            save=False
        )

        opportunity.image = None

        opportunity.save(
            update_fields=[
                "published_product",
                "status",
                "image",
                "updated_at",
            ]
        )

        return product

        
        