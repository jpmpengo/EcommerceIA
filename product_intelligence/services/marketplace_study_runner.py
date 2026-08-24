from product_intelligence.services.marketplace_collector_factory import (
    MarketplaceCollectorFactory,
)
from product_intelligence.services.marketplace_study_execution import (
    MarketplaceStudyExecutionService,
)


class MarketplaceStudyRunner:

    @staticmethod
    def run(
        study,
    ):
        collectors = (
            MarketplaceCollectorFactory
            .build(
                marketplaces=(
                    study.marketplaces
                ),
            )
        )

        service = (
            MarketplaceStudyExecutionService(
                collectors=collectors,
            )
        )

        return service.execute(
            study
        )