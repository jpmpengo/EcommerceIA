class SupplierDeliveryPolicyService:

    def __init__(
        self,
        preferred_maximum_days=10,
        absolute_maximum_days=50,
        slow_score_penalty=15,
        priority_maximum_days=20,
    ):
        if (
            preferred_maximum_days
            > priority_maximum_days
        ):
            raise ValueError(
                (
                    "Le délai préféré ne peut pas "
                    "dépasser le délai prioritaire."
                )
            )

        if (
            priority_maximum_days
            > absolute_maximum_days
        ):
            raise ValueError(
                (
                    "Le délai prioritaire ne peut pas "
                    "dépasser le délai maximum."
                )
            )

        self.preferred_maximum_days = (
            preferred_maximum_days
        )

        self.priority_maximum_days = (
            priority_maximum_days
        )

        self.absolute_maximum_days = (
            absolute_maximum_days
        )

        self.slow_score_penalty = (
            slow_score_penalty
        )

    def evaluate(
        self,
        shipping_days,
    ):
        if shipping_days is None:
            return {
                "status": "incomplete",
                "reason": (
                    "Délai de livraison manquant."
                ),
                "score_penalty": None,
            }

        if (
            shipping_days
            > self.absolute_maximum_days
        ):
            return {
                "status": "rejected",
                "reason": (
                    "Délai de livraison de "
                    f"{shipping_days} jours "
                    "supérieur au maximum accepté "
                    f"de {self.absolute_maximum_days} "
                    "jours."
                ),
                "score_penalty": None,
            }

        if (
            shipping_days
            > self.priority_maximum_days
        ):
            return {
                "status": "fallback",
                "reason": (
                    "Délai de livraison de "
                    f"{shipping_days} jours : "
                    "offre de repli uniquement."
                ),
                "score_penalty": (
                    self.slow_score_penalty
                ),
            }

        if (
            shipping_days
            > self.preferred_maximum_days
        ):
            return {
                "status": "slow",
                "reason": (
                    "Délai de livraison de "
                    f"{shipping_days} jours "
                    "supérieur au délai préféré "
                    f"de {self.preferred_maximum_days} "
                    "jours."
                ),
                "score_penalty": (
                    self.slow_score_penalty
                ),
            }

        return {
            "status": "accepted",
            "reason": "",
            "score_penalty": 0,
        }
