class CJCountryFallbackService:

    def __init__(self, cj_searcher):
        self.cj_searcher = cj_searcher

    def run(
        self,
        product_idea,
        eu_offer_results,
    ):
        has_usable_eu_offer = any(
            result.get("status") == "researched"
            for result in eu_offer_results
        )

        if has_usable_eu_offer:
            return []

        return self.cj_searcher.search_for_idea_in_country(
            product_idea=product_idea,
            country_code="CN",
        )
