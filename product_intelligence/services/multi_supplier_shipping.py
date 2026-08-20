class MultiSupplierShippingService:

    def __init__(
        self,
        estimators,
    ):
        self.estimators = estimators

    def estimate(
        self,
        offer,
        destination_country,
        quantity=1,
    ):
        for estimator in self.estimators:
            if not estimator.can_handle(
                offer
            ):
                continue

            return estimator.estimate(
                offer=offer,
                destination_country=(
                    destination_country
                ),
                quantity=quantity,
            )

        return None
