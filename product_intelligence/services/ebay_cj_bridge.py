from difflib import SequenceMatcher

class EbayCJBridgeService:

    def __init__(
        self,
        cj_pipeline_service,
        cj_client=None,
    ):
        self.cj_pipeline_service = cj_pipeline_service
        self.cj_client = cj_client

    def create_opportunity(
        self,
        market_observation,
        supplier,
        cj_product_id,
    ):
        return (
            self.cj_pipeline_service
            .build_opportunity_from_observation(
                supplier=supplier,
                product_id=cj_product_id,
                market_observation=market_observation,
            )
        )

    def select_best_product(
        self,
        market_observation,
        products,
    ):
        target_name = market_observation.name.strip().lower()

        best_product = None
        best_score = 0.0

        for product in products:
            product_name = (
                product.get("nameEn")
                or product.get("productNameEn")
                or ""
            )

            normalized_name = product_name.strip().lower()

            if normalized_name == target_name:
                return product

            score = SequenceMatcher(
                None,
                target_name,
                normalized_name,
            ).ratio()

            if score > best_score:
                best_score = score
                best_product = product

        if best_product is not None and best_score >= 0.60:
            return best_product

        raise ValueError(
            "No reliable CJ product match found."
        )

    def search_and_create_opportunity(
        self,
        market_observation,
        supplier,
    ):
        if self.cj_client is None:
            raise ValueError(
                "CJ client is required for product search."
            )

        products = self.cj_client.search_products(
            keyword=market_observation.name,
        )

        if not products:
            raise ValueError(
                "No CJ product found."
            )

        product = self.select_best_product(
            market_observation=market_observation,
            products=products,
        )

        product_id = product.get("id")

        if not product_id:
            raise ValueError(
                "CJ product has no ID."
            )

        return self.create_opportunity(
            market_observation=market_observation,
            supplier=supplier,
            cj_product_id=product_id,
        )

