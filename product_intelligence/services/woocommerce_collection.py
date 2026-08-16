class WooCommerceCollectionService:

    def __init__(
        self,
        client,
        observation_service,
    ):
        self.client = client
        self.observation_service = observation_service

    def collect(self):
        products = self.client.get_products()

        observations = []

        for product in products:
            normalized_product = (
                self.client.normalize_product(
                    product
                )
            )

            observation = (
                self.observation_service
                .create_observation(
                    product=normalized_product,
                )
            )

            observations.append(
                observation
            )

        return observations
        