from django.db import transaction

from product_intelligence.models import (
    ProductIdea,
)


class ProductIdeaSelectionService:

    MAX_SELECTED_IDEAS = 5

    @staticmethod
    @transaction.atomic
    def select(idea, selection_source="manual"):
        if selection_source not in {"manual", "automatic"}:
            raise ValueError("Origine de selection invalide.")

        locked_idea = (
            ProductIdea.objects
            .select_for_update()
            .get(
                pk=idea.pk
            )
        )

        if locked_idea.status == "selected":
            return locked_idea

        if locked_idea.status != "proposed":
            raise ValueError(
                (
                    "Seule une idée proposée "
                    "peut être sélectionnée."
                )
            )

        selected_count = (
            ProductIdea.objects
            .select_for_update()
            .filter(
                status="selected"
            )
            .count()
        )

        if (
            selected_count
            >= ProductIdeaSelectionService.MAX_SELECTED_IDEAS
        ):
            raise ValueError(
                (
                    "Cinq idées sont déjà "
                    "sélectionnées."
                )
            )

        locked_idea.status = "selected"
        locked_idea.selection_source = selection_source

        locked_idea.save(
            update_fields=[
                "status",
                "selection_source",
                "updated_at",
            ]
        )

        return locked_idea

    @staticmethod
    @transaction.atomic
    def reject(idea):
        locked_idea = (
            ProductIdea.objects
            .select_for_update()
            .get(
                pk=idea.pk
            )
        )

        if locked_idea.status == "rejected":
            return locked_idea

        if locked_idea.status not in {
            "proposed",
            "selected",
        }:
            raise ValueError(
                (
                    "Cette idée ne peut pas "
                    "être écartée."
                )
            )

        locked_idea.status = "rejected"

        locked_idea.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return locked_idea
