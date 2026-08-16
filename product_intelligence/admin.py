from django.contrib import admin, messages

from .models import ProductOpportunity

from .services.publisher import OpportunityPublisher


@admin.register(ProductOpportunity)
class ProductOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "source_name",
        "market_price",
        "supplier_price",
        "get_total_cost",
        "get_estimated_margin",
        "get_margin_percent",
        "opportunity_score",
        "status",
    )

    list_editable = (
        "status",
    )

    list_filter = (
        "status",
        "source_name",
    )

    search_fields = (
        "name",
        "source_name",
    )

    ordering = (
        "-opportunity_score",
        "-detected_at",
    )

    actions = (
        "publish_to_catalog",
    )

    @admin.display(description="Coût total")
    def get_total_cost(self, obj):
        return f"{obj.get_total_cost():.2f} €"

    @admin.display(description="Marge")
    def get_estimated_margin(self, obj):
        return f"{obj.get_estimated_margin():.2f} €"

    @admin.display(description="Marge %")
    def get_margin_percent(self, obj):
        return f"{obj.get_margin_percent():.1f} %"

    @admin.action(
        description=(
            "Publier les opportunités sélectionnées "
            "dans le catalogue"
        )
    )
    def publish_to_catalog(self, request, queryset):
        published_count = 0
        errors = []

        for opportunity in queryset:
            try:
                OpportunityPublisher.publish(opportunity)
                published_count += 1

            except ValueError as error:
                errors.append(
                    f"« {opportunity.name} » : {error}"
                )

        if published_count:
            self.message_user(
                request,
                (
                    f"{published_count} produit(s) publié(s) "
                    "dans le catalogue."
                ),
                level=messages.SUCCESS,
            )

        for error in errors:
            self.message_user(
                request,
                error,
                level=messages.WARNING,
            )
