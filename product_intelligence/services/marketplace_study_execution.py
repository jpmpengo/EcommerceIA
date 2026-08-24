from product_intelligence.models import (
    MarketplaceStudy,
)
from product_intelligence.services.market_observation_importer import (
    MarketObservationImporter,
)


class MarketplaceStudyExecutionService:

    def __init__(
        self,
        collectors,
    ):
        self.collectors = collectors

    def execute(
        self,
        study,
    ):
        study = MarketplaceStudy.objects.get(
            pk=study.pk
        )

        if study.status == "completed":
            return study

        if study.status != "draft":
            raise ValueError(
                (
                    "Seule une étude en brouillon "
                    "peut être exécutée."
                )
            )

        study.status = "running"

        study.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        try:
            for marketplace in study.marketplaces:
                collector = self.collectors.get(
                    marketplace
                )

                if collector is None:
                    raise ValueError(
                        (
                            "Aucun collecteur configuré "
                            f"pour {marketplace}."
                        )
                    )

                importer = (
                    MarketObservationImporter(
                        collector=collector
                    )
                )

                for query in study.queries:
                    importer.import_query(
                        query=query,
                        study=study,
                        max_results=(
                            study
                            .max_results_per_query
                        ),
                    )

        except Exception:
            study.status = "failed"

            study.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise

        study.status = "completed"

        study.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return study