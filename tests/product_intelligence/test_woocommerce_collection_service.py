from django.test import TestCase

from product_intelligence.models import MarketObservation
from product_intelligence.services.woocommerce_collection import (
    WooCommerceCollectionService,
)


class FakeWooCommerceClient:

    def get_products(self):
        return [
            {
                "id": 123,
                "name": "Wireless Charger",
                "price": "19.90",
                "permalink": (
                    "http://localhost:10004/"
                    "product/wireless-charger/"
                ),
            }
        ]

    def normalize_product(self, product):
        return {
            "external_id": str(product["id"]),
            "name": product["name"],
            "observed_price": product["price"],
            "currency": "EUR",
            "product_url": product["permalink"],
        }


class FakeObservationService:

    def create_observation(self, product):
        return MarketObservation.objects.create(
            source="woocommerce",
            external_id=product["external_id"],
            name=product["name"],
            observed_price=product["observed_price"],
            currency=product["currency"],
            product_url=product["product_url"],
            raw_data=product,
        )


class WooCommerceCollectionServiceTests(TestCase):

    def test_collects_products_into_market_observations(self):
        service = WooCommerceCollectionService(
            client=FakeWooCommerceClient(),
            observation_service=FakeObservationService(),
        )

        observations = service.collect()

        self.assertEqual(
            len(observations),
            1,
        )

        observation = observations[0]

        self.assertEqual(
            observation.source,
            "woocommerce",
        )

        self.assertEqual(
            observation.external_id,
            "123",
        )

        self.assertEqual(
            observation.name,
            "Wireless Charger",
        )
        