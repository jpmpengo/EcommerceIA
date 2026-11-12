class SupplierCandidateCollectionService:

    def __init__(
        self,
        search_service,
        visual_matching_service=None,
        fallback_service=None,
    ):
        self.search_service = search_service
        self.visual_matching_service = (
            visual_matching_service
        )
        self.fallback_service = fallback_service

    def collect(
        self,
        product_idea,
    ):
        if product_idea.status not in {"selected", "validated"}:
            raise ValueError(
                (
                    "La catégorie doit être "
                    "sélectionnée avant la "
                    "recherche fournisseur."
                )
            )

        offers = (
            self.search_service
            .search_for_idea(
                product_idea=product_idea,
            )
        )

        if not offers and self.fallback_service is not None:
            offers = self.fallback_service.run(
                product_idea=product_idea,
                eu_offer_results=[],
            )

        if self.visual_matching_service is not None:
            self.visual_matching_service.match(
                offers
            )

        offers_by_supplier = {}

        for offer in offers:
            supplier_name = (
                offer.supplier.name
            )

            offers_by_supplier[
                supplier_name
            ] = (
                offers_by_supplier.get(
                    supplier_name,
                    0,
                )
                + 1
            )

        return {
            "product_idea_id": (
                product_idea.id
            ),
            "suppliers_searched": len(
                self.search_service
                .supplier_searchers
            ),
            "offers_found": len(
                offers
            ),
            "offers_by_supplier": (
                offers_by_supplier
            ),
            "suppliers_unavailable": getattr(
                self.search_service,
                "supplier_failures",
                {},
            ),
        }