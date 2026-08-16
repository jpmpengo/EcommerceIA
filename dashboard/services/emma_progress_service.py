from products.models import Product


class EmmaProgressService:

    @staticmethod
    def get_progress(previous_visit):
        if previous_visit is None:
            return []

        count = (
            Product.objects
            .filter(
                created_at__gt=previous_visit,
            )
            .count()
        )

        if count == 0:
            return []

        if count == 1:
            message = (
                "Vous avez publié un nouveau produit "
                "depuis votre dernière visite."
            )
        else:
            message = (
                f"Vous avez publié {count} nouveaux produits "
                "depuis votre dernière visite."
            )

        return [
            {
                "icon": "🎉",
                "message": message,
            }
        ]

        

