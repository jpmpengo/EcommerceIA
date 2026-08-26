class MarketPriceReferenceService:

    POLICY_FIELDS = {
        "minimum": "minimum_price",
        "median": "median_price",
        "maximum": "maximum_price",
    }

    DEFAULT_POLICY = "minimum"

    @classmethod
    def select(
        cls,
        summary,
        policy=None,
    ):
        selected_policy = (
            policy
            or cls.DEFAULT_POLICY
        )

        field_name = cls.POLICY_FIELDS.get(
            selected_policy
        )

        if field_name is None:
            raise ValueError(
                (
                    "Politique de prix de "
                    "référence inconnue."
                )
            )

        selected_price = summary.get(
            field_name
        )

        if selected_price is None:
            raise ValueError(
                "Prix de référence indisponible."
            )

        return selected_price