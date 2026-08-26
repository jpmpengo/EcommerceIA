from decimal import Decimal

from django.utils import timezone


class SupplierOfferBaseCostService:

    def __init__(
        self,
        rate_client,
        conversion_service,
        clock=None,
    ):
        self.rate_client = rate_client

        self.conversion_service = (
            conversion_service
        )

        self.clock = (
            clock
            or timezone.now
        )

    def calculate(
        self,
        supplier_offer,
        target_currency,
    ):
        if supplier_offer.shipping_cost is None:
            raise ValueError(
                "Coût de livraison manquant."
            )

        source_currency = (
            supplier_offer.currency
        )

        if source_currency == target_currency:
            exchange_rate = Decimal("1")
        else:
            exchange_rate = (
                self.rate_client.get_rate(
                    from_currency=(
                        source_currency
                    ),
                    to_currency=(
                        target_currency
                    ),
                )
            )

        purchase_converted = (
            self.conversion_service.convert(
                amount=(
                    supplier_offer.purchase_price
                ),
                from_currency=source_currency,
                to_currency=target_currency,
                exchange_rate=exchange_rate,
            )
        )

        shipping_converted = (
            self.conversion_service.convert(
                amount=(
                    supplier_offer.shipping_cost
                ),
                from_currency=source_currency,
                to_currency=target_currency,
                exchange_rate=exchange_rate,
            )
        )

        base_cost = (
            purchase_converted
            + shipping_converted
        )

        return {
            "source_currency": (
                source_currency
            ),
            "target_currency": (
                target_currency
            ),
            "exchange_rate": (
                exchange_rate
            ),
            "purchase_original": (
                supplier_offer.purchase_price
            ),
            "shipping_original": (
                supplier_offer.shipping_cost
            ),
            "purchase_converted": (
                purchase_converted
            ),
            "shipping_converted": (
                shipping_converted
            ),
            "base_cost": base_cost,
            "rate_source": getattr(
                self.rate_client,
                "BASE_URL",
                "",
            ),
            "calculated_at": self.clock(),
        }