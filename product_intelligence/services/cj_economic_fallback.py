class CJEconomicFallbackService:

    def __init__(
        self,
        cj_searcher,
        research_pipeline,
        qualification_service=None,
        destination_country="FR",
        visual_matching_service=None,
    ):
        self.cj_searcher = cj_searcher
        self.research_pipeline = research_pipeline
        self.qualification_service = qualification_service
        self.destination_country = destination_country
        self.visual_matching_service = visual_matching_service

    def run(
        self,
        product_idea,
    ):
        supplier_offers = (
            self.cj_searcher.search_for_idea_in_country(
                product_idea=product_idea,
                country_code="CN",
            )
        )

        if self.visual_matching_service is not None:
            self.visual_matching_service.match(
                supplier_offers
            )
            has_visual_references = product_idea.visual_references.exists()
            supplier_offers = [
                offer
                for offer in supplier_offers
                if (
                    getattr(
                        offer,
                        "visual_match_classification",
                        "",
                    ) not in ("rejected", "weak")
                    and (
                        not has_visual_references
                        or bool(
                            getattr(
                                offer,
                                "visual_match_classification",
                                "",
                            )
                        )
                    )
                )
            ]

        researched_offers = []

        for supplier_offer in supplier_offers:
            result = self.research_pipeline.process(
                supplier_offer=supplier_offer,
                destination_country=self.destination_country,
            )

            if result.get("status") != "researched":
                continue

            if self.qualification_service is not None:
                self.qualification_service.qualify(
                    supplier_offer
                )

            researched_offers.append(
                supplier_offer
            )

        return researched_offers
