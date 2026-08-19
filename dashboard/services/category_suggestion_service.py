from products.models import Category


class CategorySuggestionService:

    @staticmethod
    def suggest(opportunity):
        text = (
            f"{opportunity.name} "
            f"{opportunity.description}"
        ).lower()

        rules = [
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

