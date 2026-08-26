class ComparablePriceCollectionRunner:

    def __init__(
        self,
        collection_service,
    ):
        self.collection_service = (
            collection_service
        )

    def run(
        self,
        product_idea,
    ):
        offers_processed = 0
        comparable_prices_saved = 0

        supplier_offers = (
            product_idea
            .supplier_offers
            .all()
        )

        for supplier_offer in supplier_offers:
            saved_prices = (
                self.collection_service.collect(
                    supplier_offer=(
                        supplier_offer
                    ),
                )
            )

            offers_processed += 1

            comparable_prices_saved += len(
                saved_prices
            )

        return {
            "offers_processed": (
                offers_processed
            ),
            "comparable_prices_saved": (
                comparable_prices_saved
            ),
        }