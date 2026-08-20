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
        target_name=None,
        target_dimensions=None,
        target_capacity_ml=None,
        dimensions_by_offer=None,
        capacity_by_offer=None,
        target_variant_data=None,
        variant_data_by_offer=None,
        target_offer=None,
    ):
        dimensions_by_offer = (
            dimensions_by_offer
            or {}
        )

        capacity_by_offer = (
            capacity_by_offer
            or {}
        )

        variant_data_by_offer = (
            variant_data_by_offer
            or {}
        )

        # L'offre cible peut fournir son nom
        # et ses caractéristiques persistées.
        if target_offer is not None:
            if target_name is None:
                target_name = (
                    target_offer.product_name
                )

            target_features = (
                target_offer.variant_features
                or {}
            )

            if target_dimensions is None:
                dimensions = (
                    target_features.get(
                        "dimensions_mm"
                    )
                )

                if dimensions:
                    target_dimensions = tuple(
                        dimensions
                    )

            if target_capacity_ml is None:
                target_capacity_ml = (
                    target_features.get(
                        "capacity_ml"
                    )
                )

        # Compatibilité avec les anciennes
        # données brutes de variante cible.
        if (
            (
                target_dimensions is None
                or target_capacity_ml is None
            )
            and target_variant_data is not None
            and self.variant_features_service
            is not None
        ):
            target_features = (
                self.variant_features_service.extract(
                    variant=target_variant_data,
                )
            )

            if target_dimensions is None:
                target_dimensions = (
                    target_features.get(
                        "dimensions_mm"
                    )
                )

            if target_capacity_ml is None:
                target_capacity_ml = (
                    target_features.get(
                        "capacity_ml"
                    )
                )

        comparable_offers = []

        for offer in offers:
            # Priorité 1 :
            # caractéristiques explicites.
            offer_dimensions = (
                dimensions_by_offer.get(
                    offer.id
                )
            )

            offer_capacity_ml = (
                capacity_by_offer.get(
                    offer.id
                )
            )

            # Priorité 2 :
            # caractéristiques persistées.
            offer_features = (
                offer.variant_features
                or {}
            )

            if offer_dimensions is None:
                dimensions = (
                    offer_features.get(
                        "dimensions_mm"
                    )
                )

                if dimensions:
                    offer_dimensions = tuple(
                        dimensions
                    )

            if offer_capacity_ml is None:
                offer_capacity_ml = (
                    offer_features.get(
                        "capacity_ml"
                    )
                )

            # Priorité 3 :
            # anciennes données brutes
            # de variante.
            if (
                (
                    offer_dimensions is None
                    or offer_capacity_ml is None
                )
                and self.variant_features_service
                is not None
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

                    if offer_dimensions is None:
                        offer_dimensions = (
                            features.get(
                                "dimensions_mm"
                            )
                        )

                    if offer_capacity_ml is None:
                        offer_capacity_ml = (
                            features.get(
                                "capacity_ml"
                            )
                        )

            is_comparable = (
                self.matching_service
                .are_products_comparable(
                    first_name=(
                        offer.product_name
                    ),
                    second_name=(
                        target_name
                    ),
                    first_dimensions=(
                        offer_dimensions
                    ),
                    second_dimensions=(
                        target_dimensions
                    ),
                    first_capacity_ml=(
                        offer_capacity_ml
                    ),
                    second_capacity_ml=(
                        target_capacity_ml
                    ),
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
