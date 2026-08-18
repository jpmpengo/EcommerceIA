class SupplierOfferComparisonService:

    def __init__(
        self,
        matching_service,
        selection_service,
    ):
        self.matching_service = (
            matching_service
        )
        self.selection_service = (
            selection_service
        )

    def select_best_comparable_offer(
        self,
        offers,
        target_name,
        target_dimensions=None,
        dimensions_by_offer=None,
    ):
        dimensions_by_offer = (
            dimensions_by_offer
            or {}
        )

        comparable_offers = []

        for offer in offers:
            offer_dimensions = (
                dimensions_by_offer.get(
                    offer.id
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
        