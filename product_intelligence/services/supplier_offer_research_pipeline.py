class SupplierOfferResearchPipeline:

    ALLOWED_DELIVERY_STATUSES = {
        "accepted",
        "slow",
        "fallback",
    }

    def __init__(
        self,
        shipping_service,
        delivery_policy,
        comparable_price_collection,
    ):
        self.shipping_service = (
            shipping_service
        )

        self.delivery_policy = (
            delivery_policy
        )

        self.comparable_price_collection = (
            comparable_price_collection
        )

    def process(
        self,
        supplier_offer,
        destination_country,
    ):
        shipping_result = (
            self.shipping_service.enrich(
                supplier_offer=supplier_offer,
                destination_country=(
                    destination_country
                ),
            )
        )

        if (
            shipping_result.get("status")
            != "estimated"
        ):
            return {
                "status": "incomplete",
                "shipping": shipping_result,
                "delivery_status": (
                    "incomplete"
                ),
                "comparable_prices_saved": 0,
            }

        delivery_result = (
            self.delivery_policy.evaluate(
                shipping_days=(
                    shipping_result.get(
                        "shipping_days"
                    )
                ),
            )
        )

        delivery_status = (
            delivery_result.get("status")
        )

        if (
            delivery_status
            not in self.ALLOWED_DELIVERY_STATUSES
        ):
            return {
                "status": delivery_status,
                "shipping": shipping_result,
                "delivery": delivery_result,
                "delivery_status": (
                    delivery_status
                ),
                "comparable_prices_saved": 0,
            }

        comparable_prices = (
            self.comparable_price_collection
            .collect(
                supplier_offer=(
                    supplier_offer
                ),
            )
        )

        return {
            "status": "researched",
            "shipping": shipping_result,
            "delivery": delivery_result,
            "delivery_status": (
                delivery_status
            ),
            "comparable_prices_saved": len(
                comparable_prices
            ),
        }
