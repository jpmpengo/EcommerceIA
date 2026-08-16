from difflib import SequenceMatcher


class WooCommerceCJBridgeService:

    def __init__(
        self,
        cj_pipeline_service,
        cj_client,
    ):
        self.cj_pipeline_service = cj_pipeline_service
        self.cj_client = cj_client

    def search_and_create_opportunity(
        self,
        market_observation,
        supplier,
    ):
        return self.build_opportunity(
            supplier=supplier,
            market_observation=market_observation,
        )

    def build_opportunity(
        self,
        supplier,
        market_observation,
    ):
        products = self.cj_client.search_products(
            keyword=market_observation.name,
        )

        if not products:
            return None

        observation_name = (
            market_observation.name
            .strip()
            .lower()
        )

        best_product = None
        best_score = 0.0

        for candidate in products:
            candidate_name = (
                candidate.get("productNameEn")
                or candidate.get("nameEn")
                or candidate.get("name")
                or ""
            ).strip().lower()

            if candidate_name == observation_name:
                best_product = candidate
                best_score = 1.0
                break

            score = SequenceMatcher(
                None,
                observation_name,
                candidate_name,
            ).ratio()

            if score > best_score:
                best_score = score
                best_product = candidate

        if best_product is None or best_score < 0.60:
            return None

        product_id = (
            best_product.get("pid")
            or best_product.get("id")
        )

        if not product_id:
            return None

        return (
            self.cj_pipeline_service
            .build_opportunity_from_observation(
                supplier=supplier,
                product_id=product_id,
                market_observation=market_observation,
            )
        )

        
        

        