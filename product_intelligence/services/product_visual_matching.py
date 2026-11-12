class ProductVisualMatchingService:

    def __init__(
        self,
        client,
    ):
        self.client = client

    def match(
        self,
        references,
        supplier_offers,
        product_idea_name=None,
    ):
        usable_references = [
            reference
            for reference in references
            if reference.get("image_url")
        ]

        candidates = [
            {
                "offer_id": offer.id,
                "product_name": offer.product_name,
                "image_url": offer.image_url,
            }
            for offer in supplier_offers
            if offer.image_url
        ]

        if not usable_references or not candidates:
            return {
                "matches": [],
            }

        kwargs = dict(references=usable_references, candidates=candidates)
        if product_idea_name is not None:
            kwargs["product_idea_name"] = product_idea_name
        return self.client.match(**kwargs)
