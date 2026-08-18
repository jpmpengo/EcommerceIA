class SupplierOfferComparisonService:

    def __init__(
        self,
        matching_service,
        selection_service,
        variant_features_service=None,
    ):
        self.matching_service = (
            matching_service
        )

        self.selection_service = (
            selection_service
        )

        self.variant_features_service = (
            variant_features_service
        )

    def select_best_comparable_offer(
        self,
        offers,
        target_name,
        target_dimensions=None,
        dimensions_by_offer=None,
        target_variant_data=None,
        variant_data_by_offer=None,
    ):
        dimensions_by_offer = (
            dimensions_by_offer
            or {}
        )

        variant_data_by_offer = (
            variant_data_by_offer
            or {}
        )

        if (
            target_dimensions is None
            and target_variant_data is not None
            and self.variant_features_service is not None
        ):
            target_features = (
                self.variant_features_service.extract(
                    variant=target_variant_data,
                )
            )

            target_dimensions = (
                target_features.get(
                    "dimensions_mm"
                )
            )

        comparable_offers = []

        for offer in offers:
            offer_dimensions = (
                dimensions_by_offer.get(
                    offer.id
                )
            )

            if (
                offer_dimensions is None
                and self.variant_features_service is not None
            ):
                variant_data = (
                    variant_data_by_offer.get(
                        offer.id
                    )
                )

                if variant_data is not None:
                    features = (
                        self.variant_features_service.extract(
                            variant=variant_data,
                        )
                    )

                    offer_dimensions = (
                        features.get(
                            "dimensions_mm"
                        )
                    )

            is_comparable = (
                self.matching_service
                .are_products_comparable(
                    first_name=offer.product_name,
                    second_name=target_name,
                    first_dimensions=offer_dimensions,
                    second_dimensions=target_dimensions,
                )
            )

            if is_comparable:
                comparable_offers.append(
                    offer
                )

        return (
            self.selection_service
            .select_best_offer(
                comparable_offers
            )
        )

        
        