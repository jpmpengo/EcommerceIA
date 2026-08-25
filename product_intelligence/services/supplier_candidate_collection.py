class SupplierCandidateCollectionService:

    def __init__(
        self,
        search_service,
    ):
        self.search_service = search_service

    def collect(
        self,
        product_idea,
    ):
        if product_idea.status != "selected":
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
        }