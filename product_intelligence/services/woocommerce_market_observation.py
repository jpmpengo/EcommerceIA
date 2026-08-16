from decimal import Decimal

from product_intelligence.models import MarketObservation


class WooCommerceMarketObservationService:

    def create_observation(
        self,
        product,
    ):
        observation, _ = MarketObservation.objects.update_or_create(
            source="woocommerce",
            external_id=product["external_id"],
            defaults={
                "name": product["name"],
                "observed_price": Decimal(
                    product["observed_price"]
                ),
                "currency": product["currency"],
                "product_url": product["product_url"],
                "raw_data": product,
            },
        )

        return observation

        