class SupplierCatalogImportService:

    def __init__(
        self,
        importers,
    ):
        self.importers = importers

    def import_catalog(
        self,
    ):
        offers = []

        for importer in self.importers:
            try:
                imported_offers = (
                    importer.import_offers()
                )
            except Exception:
                continue

            offers.extend(
                imported_offers
            )

        return offers

        


