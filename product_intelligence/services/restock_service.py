class RestockService:

    @staticmethod
    def restock(
        opportunity,
        quantity,
    ):
        if opportunity.restock_product is None:
            raise ValueError(
                "This opportunity is not a restock opportunity."
            )

        if opportunity.status != "approved":
            raise ValueError(
                "This restock opportunity must be approved."
            )

        if quantity <= 0:
            raise ValueError(
                "Restock quantity must be greater than zero."
            )

        product = opportunity.restock_product

        product.stock += quantity
        product.is_available = True

        product.save(
            update_fields=[
                "stock",
                "is_available",
            ]
        )

        # Le réapprovisionnement est terminé :
        # l'opportunité ne doit plus rester active.
        opportunity.status = "restocked"

        opportunity.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return product
        