class StockSuggestionService:

    MAX_INITIAL_STOCK = 10

    @staticmethod
    def suggest(opportunity):
        supplier_offer = getattr(
            opportunity,
            "supplier_offer",
            None,
        )

        if supplier_offer is None:
            return None

        stock = supplier_offer.stock

        if stock is None or stock <= 0:
            return None

        return min(
            stock,
            StockSuggestionService.MAX_INITIAL_STOCK,
        )
        