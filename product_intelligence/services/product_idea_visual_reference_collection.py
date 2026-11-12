from django.db import transaction

from product_intelligence.models import ProductIdeaVisualReference
from product_intelligence.services.visual_image_accessibility import VisualImageAccessibilityService


class ProductIdeaVisualReferenceCollectionService:

    def __init__(self, search_service, model_name=""):
        self.search_service = search_service
        self.model_name = model_name

    @transaction.atomic
    def collect(self, product_idea):
        result = self.search_service.search(
            product_idea=product_idea,
        )

        valid_references = [reference for reference in result.get("visual_references", []) if VisualImageAccessibilityService.is_accessible(reference.get("image_url", ""))]
        if not valid_references:
            return []

        ProductIdeaVisualReference.objects.filter(
            product_idea=product_idea,
        ).delete()

        references = [
            ProductIdeaVisualReference(
                product_idea=product_idea,
                supplier_search_keyword=reference["supplier_search_keyword"],
                product_name=reference.get("product_name", ""),
                source_title=reference.get("source_title", ""),
                source_url=reference.get("source_url", ""),
                image_url=reference["image_url"],
                model_name=self.model_name,
            )
            for reference in result.get("visual_references", [])
        ]

        return ProductIdeaVisualReference.objects.bulk_create(
            references
        )
