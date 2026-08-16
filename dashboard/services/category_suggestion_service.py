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
        ]

        for keywords, category_name in rules:
            if any(keyword in text for keyword in keywords):
                return Category.objects.filter(
                    name__iexact=category_name
                ).first()

        return None

