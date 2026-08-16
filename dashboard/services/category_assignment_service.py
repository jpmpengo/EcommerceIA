class CategoryAssignmentService:

    @staticmethod
    def assign(opportunity, category):
        opportunity.category = category
        opportunity.save(
            update_fields=["category"]
        )

        return opportunity

        