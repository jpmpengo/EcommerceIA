class PublicationReadinessService:

    @staticmethod
    def evaluate(opportunity):
        missing = []

        if opportunity.category is None:
            missing.append(
                {
                    "field": "category",
                    "label": "Catégorie",
                    "message": (
                        "Choisissez une catégorie "
                        "pour publier ce produit."
                    ),
                }
            )

        description = (
            opportunity.description or ""
        ).strip()

        if len(description) < 50:
            missing.append(
                {
                    "field": "description",
                    "label": "Description",
                    "message": (
                        "La description doit être enrichie "
                        "avant la publication."
                    ),
                }
            )

        if not opportunity.image:
            missing.append(
                {
                    "field": "image",
                    "label": "Image",
                    "message": (
                        "Une image doit être ajoutée "
                        "avant la publication."
                    ),
                }
            )

        if opportunity.initial_stock <= 0:
            missing.append(
                {
                    "field": "initial_stock",
                    "label": "Stock initial",
                    "message": "Définissez un stock initial avant la publication.",
                }
            )
        
        return {
            "ready": len(missing) == 0,
            "missing": missing,
        }



        