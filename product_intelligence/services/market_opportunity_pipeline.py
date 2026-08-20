class MarketOpportunityPipelineService:

    def __init__(
        self,
        supplier_search_service,
        comparison_service,
        opportunity_service,
        currency_conversion_service=None,
        exchange_rate_client=None,
        variant_features_service=None,
    ):
        self.supplier_search_service = (
            supplier_search_service
        )

        self.comparison_service = (
            comparison_service
        )

        self.opportunity_service = (
            opportunity_service
        )

        self.currency_conversion_service = (
            currency_conversion_service
        )

        self.exchange_rate_client = (
            exchange_rate_client
        )

        self.variant_features_service = (
            variant_features_service
        )

    def process(
        self,
        market_observation,
    ):
        if (
            market_observation.observed_price
            is None
        ):
            return None

        offers = (
            self.supplier_search_service.search(
                market_observation=(
                    market_observation
                ),
            )
        )

        target_dimensions = None
        target_capacity_ml = None

        if (
            self.variant_features_service
            is not None
        ):
            target_features = (
                self.variant_features_service.extract(
                    variant={
                        "name": (
                            market_observation.name
                        ),
                    }
                )
            )

            target_dimensions = (
                target_features.get(
                    "dimensions_mm"
                )
            )

            target_capacity_ml = (
                target_features.get(
                    "capacity_ml"
                )
            )

        comparison_arguments = {
            "offers": offers,
            "target_name": (
                market_observation.name
            ),
        }

        if target_dimensions is not None:
            comparison_arguments[
                "target_dimensions"
            ] = target_dimensions

        if target_capacity_ml is not None:
            comparison_arguments[
                "target_capacity_ml"
            ] = target_capacity_ml

        best_offer = (
            self.comparison_service
            .select_best_comparable_offer(
                **comparison_arguments
            )
        )

        if best_offer is None:
            return None

        offer_currency = getattr(
            best_offer,
            "currency",
            None,
        )

        market_currency = getattr(
            market_observation,
            "currency",
            None,
        )

        currencies_are_known = (
            isinstance(
                offer_currency,
                str,
            )
            and isinstance(
                market_currency,
                str,
            )
        )

        if (
            currencies_are_known
            and offer_currency
            != market_currency
        ):
            if (
                self.currency_conversion_service
                is None
                or self.exchange_rate_client
                is None
            ):
                raise ValueError(
                    "Supplier and market currencies must match."
                )

            exchange_rate = (
                self.exchange_rate_client.get_rate(
                    from_currency=(
                        offer_currency
                    ),
                    to_currency=(
                        market_currency
                    ),
                )
            )

            converted_price = (
                self.currency_conversion_service.convert(
                    amount=(
                        best_offer.purchase_price
                    ),
                    from_currency=(
                        offer_currency
                    ),
                    to_currency=(
                        market_currency
                    ),
                    exchange_rate=(
                        exchange_rate
                    ),
                )
            )

            converted_shipping_cost = (
                self.currency_conversion_service.convert(
                    amount=(
                        best_offer.shipping_cost
                    ),
                    from_currency=(
                        offer_currency
                    ),
                    to_currency=(
                        market_currency
                    ),
                    exchange_rate=(
                        exchange_rate
                    ),
                )
            )

            best_offer.purchase_price = (
                converted_price
            )

            best_offer.shipping_cost = (
                converted_shipping_cost
            )

            best_offer.currency = (
                market_currency
            )

            best_offer.save(
                update_fields=[
                    "purchase_price",
                    "shipping_cost",
                    "currency",
                ]
            )

        return (
            self.opportunity_service
            .create_opportunity(
                offer=best_offer,
                market_price=(
                    market_observation
                    .observed_price
                ),
            )
        )
