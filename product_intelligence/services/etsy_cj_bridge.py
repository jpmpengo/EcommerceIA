from difflib import SequenceMatcher

class EtsyCJBridgeService:

    def __init__(
        self,
        cj_pipeline_service,
        cj_client,
    ):
        self.cj_pipeline_service = cj_pipeline_service
        self.cj_client = cj_client

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
                product.get("name")
                or product.get("nameEn")
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

            target_tokens = self._normalized_tokens(
                target_name
            )

            product_tokens = self._normalized_tokens(
                normalized_name
            )

            token_score = 0.0

            if target_tokens:
                token_score = (
                    len(target_tokens & product_tokens)
                    / len(target_tokens)
                 )

            score = max(
                score,
                token_score,
            )

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

        product_id = (
            product.get("id")
            or product.get("pid")
        )

        if not product_id:
            raise ValueError(
                "CJ product has no ID."
            )

        return (
            self.cj_pipeline_service
            .build_opportunity_from_observation(
                supplier=supplier,
                product_id=product_id,
                market_observation=market_observation,
            )
        )

    def _normalized_tokens(self, text):
        stop_words = {
            "with",
            "and",
            "the",
            "for",
            "mit",
            "und",
            "individuell",
            "personalisiert",
            "gravur",
            "motiv",
            "namen",
            "logo",
        }

        tokens = (
            text
            .lower()
            .replace(",", " ")
            .replace("-", " ")
            .split()
        )

        return {
            token
            for token in tokens
            if len(token) >= 3
            and token not in stop_words
        }

