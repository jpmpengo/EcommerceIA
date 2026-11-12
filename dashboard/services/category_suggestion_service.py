from products.models import Category


class CategorySuggestionService:

    @staticmethod
    def suggest(opportunity):
        product_idea = getattr(getattr(opportunity, "supplier_offer", None), "product_idea", None)

        category_path = getattr(product_idea, "category_path", []) or []
        for category_name in reversed(category_path):
            category = Category.objects.filter(name__iexact=category_name).first()
            if category is not None:
                return category

        product_idea_name = getattr(product_idea, "name", "")
        text = (
            f"{opportunity.name} "
            f"{opportunity.description} "
            f"{product_idea_name}"
        ).lower()

        rules = [
            (["jardin", "jardinage"], "Jardin"),
            (
                [
                    "ordinateur",
                    "portable",
                    "souris",
                    "clavier",
                    "informatique",
                    "mouse pad",
                    "mouse mat",
                    "desk mat",
                ],
                "Informatique",
            ),
            (
                [
                    "casque",
                    "écouteur",
                    "bluetooth",
                    "enceinte",
                    "audio",
                ],
                "Audio",
            ),
            (
                [
                    "wireless charger",
                    "chargeur sans fil",
                    "charger",
                    "chargeur",
                    "charging",
                ],
                "Électronique",
            ),
            (
                [
                    "mug",
                    "coffee cup",
                    "ceramic cup",
                    "tasse",
                ],
                "Maison & Cuisine",
            ),
            (
                [
                    "tote bag",
                    "canvas tote",
                    "cotton bag",
                    "sac cabas",
                ],
                "Mode & Accessoires",
            ),
        ]

        for keywords, category_name in rules:
            if any(keyword in text for keyword in keywords):
                return Category.objects.filter(
                    name__iexact=category_name
                ).first()

        return None

