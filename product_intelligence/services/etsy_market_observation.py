from decimal import Decimal

from product_intelligence.models import MarketObservation


class EtsyMarketObservationService:

    def create_observation(
        self,
        listing,
    ):
        observation, _ = MarketObservation.objects.update_or_create(
            source="etsy",
            external_id=listing["external_id"],
            defaults={
                "name": listing["name"],
                "observed_price": Decimal(
                    listing["observed_price"]
                ),
                "currency": listing["currency"],
                "product_url": listing["product_url"],
                "raw_data": listing,
            },
        )

        return observation

        