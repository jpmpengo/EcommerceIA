from django.db import transaction

from product_intelligence.models import (
    MarketplaceStudy,
    ProductIdea,
)


class MarketplaceStudyService:

    MAX_MARKETPLACES = 2
    MAX_QUERIES = 5
    MAX_PAGES_PER_MARKETPLACE = 2
    MAX_RESULTS_PER_QUERY = 20
    ALLOWED_MARKETPLACES = {
        "etsy",
        "woocommerce_local",
    }

    @staticmethod
    @transaction.atomic
    def prepare(
        idea,
        marketplaces,
    ):
        locked_idea = (
            ProductIdea.objects
            .select_for_update()
            .get(
                pk=idea.pk
            )
        )

        if locked_idea.status != "selected":
            raise ValueError(
                (
                    "Seule une idée sélectionnée "
                    "peut être étudiée."
                )
            )

        normalized_marketplaces = list(
            dict.fromkeys(
                marketplace
                .strip()
                .lower()
                for marketplace
                in marketplaces
                if marketplace.strip()
            )
        )

        if not normalized_marketplaces:
            raise ValueError(
                (
                    "Au moins une marketplace "
                    "doit être sélectionnée."
                )
            )

        if (
            len(normalized_marketplaces)
            > MarketplaceStudyService
            .MAX_MARKETPLACES
        ):
            raise ValueError(
                (
                    "Deux marketplaces maximum "
                    "sont autorisées."
                )
            )

        unsupported_marketplaces = [
            marketplace
            for marketplace
            in normalized_marketplaces
            if marketplace
            not in MarketplaceStudyService
            .ALLOWED_MARKETPLACES
        ]

        if unsupported_marketplaces:
            raise ValueError(
                (
                    "Marketplace non autorisée : "
                    f"{unsupported_marketplaces[0]}."
                )
            )

        queries = [
            query.strip()
            for query
            in locked_idea.search_keywords
            if query.strip()
        ][
            :MarketplaceStudyService
            .MAX_QUERIES
        ]

        if not queries:
            raise ValueError(
                (
                    "Cette idée ne contient aucune "
                    "requête de recherche."
                )
            )

        existing_study = (
            MarketplaceStudy.objects
            .select_for_update()
            .filter(
                product_idea=locked_idea,
                status="draft",
            )
            .order_by(
                "-created_at"
            )
            .first()
        )

        if existing_study is not None:
            existing_study.marketplaces = (
                normalized_marketplaces
            )
            existing_study.queries = queries
            existing_study.max_pages_per_marketplace = (
                MarketplaceStudyService
                .MAX_PAGES_PER_MARKETPLACE
            )
            existing_study.max_results_per_query = (
                MarketplaceStudyService
                .MAX_RESULTS_PER_QUERY
            )

            existing_study.save(
                update_fields=[
                    "marketplaces",
                    "queries",
                    "max_pages_per_marketplace",
                    "max_results_per_query",
                    "updated_at",
                ]
            )

            return existing_study

        return MarketplaceStudy.objects.create(
            product_idea=locked_idea,
            marketplaces=normalized_marketplaces,
            queries=queries,
            max_pages_per_marketplace=(
                MarketplaceStudyService
                .MAX_PAGES_PER_MARKETPLACE
            ),
            max_results_per_query=(
                MarketplaceStudyService
                .MAX_RESULTS_PER_QUERY
            ),
            status="draft",
        )