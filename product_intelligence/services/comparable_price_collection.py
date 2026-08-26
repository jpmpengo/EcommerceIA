from product_intelligence.services.comparable_price_persistence import (
    ComparablePricePersistenceService,
)


class ComparablePriceCollectionService:

    def __init__(
        self,
        search_service,
        model_name,
        persistence_service=None,
    ):
        self.search_service = (
            search_service
        )

        self.model_name = model_name

        self.persistence_service = (
            persistence_service
            or ComparablePricePersistenceService
        )

    def collect(
        self,
        supplier_offer,
    ):
        result = self.search_service.search(
            supplier_offer
        )

        comparables = result.get(
            "comparables",
            [],
        )

        if not comparables:
            return []

        return self.persistence_service.save(
            supplier_offer=(
                supplier_offer
            ),
            results=comparables,
            search_query=(
                supplier_offer.product_name
            ),
            model_name=self.model_name,
        )