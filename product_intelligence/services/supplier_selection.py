class SupplierSelectionService:

    def __init__(
        self,
        currency_conversion_service=None,
        exchange_rate_client=None,
        target_currency=None,
    ):
        self.currency_conversion_service = (
            currency_conversion_service
        )

        self.exchange_rate_client = (
            exchange_rate_client
        )

        self.target_currency = (
            target_currency
        )

        self._exchange_rate_cache = {}

    def select_best_offer(
        self,
        offers=None,
    ):
        # Compatibilité avec l'ancien appel :
        #
        # SupplierSelectionService.select_best_offer(
        #     offers
        # )
        #
        # tout en permettant maintenant :
        #
        # service = SupplierSelectionService(...)
        # service.select_best_offer(offers)

        if offers is None:
            offers = self

            service = SupplierSelectionService()

            return service._select_best_offer(
                offers
            )

        return self._select_best_offer(
            offers
        )

    def _select_best_offer(
        self,
        offers,
    ):
        eligible_offers = [
            offer
            for offer in offers
            if (
                offer.stock is not None
                and offer.stock > 0
            )
        ]

        if not eligible_offers:
            return None

        currencies = {
            offer.currency
            for offer in eligible_offers
        }

        # Toutes les offres utilisent déjà
        # la même devise.
        if len(currencies) == 1:
            return min(
                eligible_offers,
                key=lambda offer: (
                    self._raw_total_cost(
                        offer
                    ),
                    -offer.stock,
                ),
            )

        # Plusieurs devises :
        # il faut pouvoir convertir.
        if (
            self.currency_conversion_service is None
            or self.exchange_rate_client is None
            or self.target_currency is None
        ):
            raise ValueError(
                "Supplier offers must use the same currency."
            )

        return min(
            eligible_offers,
            key=lambda offer: (
                self._comparable_total_cost(
                    offer
                ),
                -offer.stock,
            ),
        )

    @staticmethod
    def _raw_total_cost(
        offer,
    ):
        return (
            offer.purchase_price
            + offer.shipping_cost
        )

    def _comparable_total_cost(
        self,
        offer,
    ):
        total_cost = self._raw_total_cost(
            offer
        )

        # Aucun besoin de conversion
        # lorsque l'offre utilise déjà
        # la devise cible.
        if offer.currency == self.target_currency:
            return total_cost

        rate_key = (
            offer.currency,
            self.target_currency,
        )

        # Le même taux n'est récupéré
        # qu'une seule fois par instance
        # du service.
        if (
            rate_key
            not in self._exchange_rate_cache
        ):
            self._exchange_rate_cache[
                rate_key
            ] = (
                self.exchange_rate_client.get_rate(
                    from_currency=offer.currency,
                    to_currency=self.target_currency,
                )
            )

        exchange_rate = (
            self._exchange_rate_cache[
                rate_key
            ]
        )

        return (
            self.currency_conversion_service.convert(
                amount=total_cost,
                from_currency=offer.currency,
                to_currency=self.target_currency,
                exchange_rate=exchange_rate,
            )
        )







