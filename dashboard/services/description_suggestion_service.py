class DescriptionSuggestionService:

    @staticmethod
    def suggest(opportunity):
        name = (opportunity.name or "").strip()

        if not name:
            return None

        original_description = (
            opportunity.description or ""
        ).strip()

        category_name = None

        if opportunity.category:
            category_name = opportunity.category.name

        parts = [
            (
                f"Découvrez {name}, un produit pensé "
                "pour répondre à vos besoins au quotidien."
            )
        ]

        if category_name:
            parts.append(
                (
                    f"Il appartient à la catégorie "
                    f"{category_name}."
                )
            )

        if original_description:
            parts.append(
                original_description
            )

        parts.append(
            (
                "Une solution pratique à découvrir "
                "pour compléter votre équipement."
            )
        )

        return " ".join(parts)

        
        