from decimal import Decimal, InvalidOperation

class CJPipelineService:

    def __init__(
        self,
        client,
        offer_service=None,
        opportunity_service=None,
        currency_conversion_service=None,
        exchange_rate=None,
        exchange_rate_client=None,
    ):
        self.client = client
        self.offer_service = offer_service
        self.opportunity_service = opportunity_service
        self.currency_conversion_service = currency_conversion_service
        self.exchange_rate = exchange_rate
        self.exchange_rate_client = exchange_rate_client

    def build_supplier_product(self, product_id):
        product_detail = self.client.get_product_detail(
            product_id=product_id,
        )

        product = self.client.normalize_product(
            product_detail,
        )

        variants = self.client.get_product_variants(
            product_id=product_id,
        )

        if variants:
            variant = variants[0]

            variant_price = variant.get("variantSellPrice")

            if variant_price is not None:
                product["purchase_price"] = variant_price

            stock = self.client.get_variant_stock(
                variant_id=variant["vid"],
            )

            product["stock"] = stock

        self._validate_single_purchase_price(
            product
        )
        
        return product

    def build_supplier_offer(
        self,
        supplier,
        product_id,
        market_observation=None,
    ):
        product = self.build_supplier_product(
            product_id=product_id,
        )

        offer = self.offer_service.create_offer(
            supplier=supplier,
            product=product,
        )

        offer.market_observation = market_observation
        offer.save(
            update_fields=[
                "market_observation",
            ]
        )

        return offer

    def build_product_opportunity(
        self,
        supplier,
        product_id,
        market_price,
    ):
        offer = self.build_supplier_offer(
            supplier=supplier,
            product_id=product_id,
        )

        return self.opportunity_service.create_opportunity(
            offer=offer,
            market_price=market_price,
        )

    def build_opportunity_from_observation(
        self,
        supplier,
        product_id,
        market_observation,
    ):
        if market_observation.observed_price is None:
            raise ValueError(
                "Market observation must have an observed price."
            )

        offer = self.build_supplier_offer(
            supplier=supplier,
            product_id=product_id,
            market_observation=market_observation,
        )

        if offer.currency != market_observation.currency:
            if self.currency_conversion_service is None:
                raise ValueError(
                    "Supplier and market currencies must match."
                )

            exchange_rate = self.exchange_rate

            if (
                exchange_rate is None
                and self.exchange_rate_client is not None
            ):
                exchange_rate = self.exchange_rate_client.get_rate(
                    from_currency=offer.currency,
                    to_currency=market_observation.currency,
                )

            if exchange_rate is None:
                raise ValueError(
                    "Supplier and market currencies must match."
                )

            converted_price = self.currency_conversion_service.convert(
                amount=offer.purchase_price,
                from_currency=offer.currency,
                to_currency=market_observation.currency,
                exchange_rate=exchange_rate,
            )

            offer.purchase_price = converted_price
            offer.currency = market_observation.currency

            offer.save(
                update_fields=[
                    "purchase_price",
                    "currency",
                ]
            )

        return self.opportunity_service.create_opportunity(
            offer=offer,
            market_price=market_observation.observed_price,
        )

    def build_supplier_offer_from_variant(
        self,
        supplier,
        product,
        variant,
    ):
        variant_id = variant["vid"]

        stock = self.client.get_variant_stock(
            variant_id=variant_id,
        )

        return self.offer_service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
            stock=stock,
        )

    def build_opportunity_from_variant(
        self,
        supplier,
        product,
        variant,
        market_observation,
    ):
        if market_observation.observed_price is None:
            raise ValueError(
                "Market observation must have an observed price."
            )

        offer = self.build_supplier_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        offer.market_observation = market_observation
        offer.save(
            update_fields=[
                "market_observation",
            ]
        )

        if offer.currency != market_observation.currency:
            if self.currency_conversion_service is None:
                raise ValueError(
                    "Supplier and market currencies must match."
                )

            exchange_rate = self.exchange_rate

            if (
                exchange_rate is None
                and self.exchange_rate_client is not None
            ):
                exchange_rate = self.exchange_rate_client.get_rate(
                    from_currency=offer.currency,
                    to_currency=market_observation.currency,
                )

            if exchange_rate is None:
                raise ValueError(
                    "Supplier and market currencies must match."
                )

            converted_price = self.currency_conversion_service.convert(
                amount=offer.purchase_price,
                from_currency=offer.currency,
                to_currency=market_observation.currency,
                exchange_rate=exchange_rate,
            )

            offer.purchase_price = converted_price
            offer.currency = market_observation.currency

            offer.save(
                update_fields=[
                    "purchase_price",
                    "currency",
                ]
            )

        return self.opportunity_service.create_opportunity(
            offer=offer,
            market_price=market_observation.observed_price,
        )

    @staticmethod
    def _validate_single_purchase_price(product):
        purchase_price = product.get(
            "purchase_price"
        )

        if purchase_price is None:
            raise ValueError(
                "CJ product price must be a single numeric value."
            )

        try:
            Decimal(
                str(purchase_price)
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "CJ product price must be a single numeric value."
            )

    @staticmethod
    def _validate_single_purchase_price(product):
        purchase_price = product.get(
            "purchase_price"
        )

        if purchase_price is None:
            raise ValueError(
                "CJ product price must be a single numeric value."
            )

        try:
            Decimal(
                str(purchase_price)
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "CJ product price must be a single numeric value."
            )


        