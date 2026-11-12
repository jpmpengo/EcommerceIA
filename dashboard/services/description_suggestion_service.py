class DescriptionSuggestionService:

    @staticmethod
    def suggest(opportunity):
        from dashboard.services.commercial_name_suggestion_service import CommercialNameSuggestionService
        name = (CommercialNameSuggestionService.suggest(opportunity) or opportunity.name or "").strip()

        if not name:
            return None

        original_description = (
            opportunity.description or ""
        ).strip()

        generated_markers = (
            "un produit pensé pour répondre à vos besoins au quotidien",
            "une solution pratique à découvrir pour compléter votre équipement",
        )
        if any(marker in original_description.lower() for marker in generated_markers):
            original_description = ""

        internal_markers = (
            "simulation locale",
            "coût rendu",
            "prix de marché",
            "prix marché",
            "achat ",
            "livraison ",
            "droits de douane",
            "tva",
        )
        if any(marker in original_description.lower() for marker in internal_markers):
            original_description = ""

        category_name = None

        if opportunity.category:
            category_name = opportunity.category.name

        product_idea = getattr(getattr(opportunity, "supplier_offer", None), "product_idea", None)
        customer_problem = (getattr(product_idea, "customer_problem", "") or "").strip()
        target_customer = (getattr(product_idea, "target_customer", "") or "").strip()

        parts = [
            (
                f"Découvrez {name}, un produit pensé "
                "pour répondre à vos besoins au quotidien."
            )
        ]

        if customer_problem:
            parts.append(customer_problem)

        if target_customer:
            parts.append(f"Ce produit s’adresse notamment aux {target_customer}")

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

        
        