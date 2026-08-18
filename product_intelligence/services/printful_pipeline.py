class PrintfulPipelineService:

    def __init__(
        self,
        client,
        offer_service=None,
    ):
        self.client = client
        self.offer_service = offer_service

    def build_supplier_offer(
        self,
        supplier,
        product_id,
    ):
        result = self.client.get_product(
            product_id=product_id,
        )

        product = result["product"]

        variants = result.get(
            "variants",
            [],
        )

        if not variants:
            raise ValueError(
                "Printful product has no variants."
            )

        variant = variants[0]

        return self.offer_service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

    def build_supplier_offer_from_variant(
        self,
        supplier,
        product,
        variant,
    ):
        return self.offer_service.create_offer_from_variant(
            supplier=supplier,
            product=product,
            variant=variant,
        )

        

        