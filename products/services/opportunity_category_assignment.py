from django.db import transaction
from products.services.category_validation import CategoryValidationService
from products.services.category_hierarchy import CategoryHierarchyService


class OpportunityCategoryAssignmentService:
    @classmethod
    @transaction.atomic
    def assign(cls, opportunity, category_path, category_reason=""):
        if not isinstance(category_reason, str) or not category_reason.strip():
            return False
        if not CategoryValidationService.validate(category_path):
            return False
        category = CategoryHierarchyService.create_approved_path(category_path)
        opportunity.category = category
        opportunity.save(update_fields=["category"])
        return True
