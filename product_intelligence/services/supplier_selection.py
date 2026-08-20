class SupplierSelectionService:

    def __init__(
        self,
        currency_conversion_service=None,
        exchange_rate_client=None,
        target_currency=None,
        max_shipping_days=None,
        target_shipping_country=None,
        shipping_estimation_service=None,
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

        self.max_shipping_days = (
            max_shipping_days
        )

        self.target_shipping_country = (
            target_shipping_country
        )

        self._exchange_rate_cache = {}

        self.shipping_estimation_service = (
            shipping_estimation_service
        )

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

        offers = list(
            offers
        )

        self._estimate_shipping(
            offers
        )

        eligible_offers = [
            offer
            for offer in offers
            if (
                offer.shipping_cost
                is not None
                and
                self._is_offer_available(
                    offer
                )
                and (
                    self.max_shipping_days is None
                    or (
                        offer.shipping_days is not None
                        and offer.shipping_days
                        <= self.max_shipping_days
                    )
                )
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
                    self._shipping_days_sort_value(
                        offer
                    ),
                    self._shipping_country_sort_value(
                        offer
                    ),
                    self._stock_sort_value(
                        offer
                    ),
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
                self._shipping_days_sort_value(
                    offer
                ),
                self._shipping_country_sort_value(
                    offer
                ),
                self._stock_sort_value(
                    offer
                ),
            ),
        )

    def _estimate_shipping(
        self,
        offers,
    ):
        if (
            self.shipping_estimation_service
            is None
        ):
            return

        for offer in offers:
            quote = (
                self.shipping_estimation_service
                .estimate(
                    offer=offer,
                    destination_country=(
                        self.target_shipping_country
                        or "FR"
                    ),
                    quantity=1,
                )
            )

            if quote is None:
                offer.shipping_cost = None
                continue

            quote_currency = quote.get(
                "currency"
            )

            if (
                quote_currency
                and quote_currency
                != offer.currency
            ):
                offer.shipping_cost = None
                continue

            offer.shipping_cost = quote.get(
                "cost"
            )
            offer.shipping_days = quote.get(
                "shipping_days"
            )
            offer.shipping_country = (
                quote.get(
                    "shipping_country"
                )
                or self.target_shipping_country
                or "FR"
            )

            offer.save(
                update_fields=[
                    "shipping_cost",
                    "shipping_days",
                    "shipping_country",
                ]
            )

    @staticmethod
    def _shipping_days_sort_value(
        offer,
    ):
        if offer.shipping_days is None:
            return float("inf")

        return offer.shipping_days

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

    def _shipping_country_sort_value(
        self,
        offer,
    ):
        if not self.target_shipping_country:
            return 0

        if (
            offer.shipping_country
            == self.target_shipping_country
        ):
            return 0

        return 1

    @staticmethod
    def _is_offer_available(
        offer,
    ):
        if offer.is_available is False:
            return False

        if (
            offer.stock is not None
            and offer.stock > 0
        ):
            return True

        if (
            offer.stock is None
            and offer.is_available is True
        ):
            return True

        return False

    @staticmethod
    def _stock_sort_value(
        offer,
    ):
        if offer.stock is None:
            return 0

        return -offer.stock
