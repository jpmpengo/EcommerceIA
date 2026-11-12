from product_intelligence.models import ProductOpportunity


class EmmaChangesService:
    @staticmethod
    def get_changes(previous_visit):
        if previous_visit is None:
            return []

        new_opportunities_count = (
            ProductOpportunity.objects
            .filter(
                detected_at__gt=previous_visit,
                status="review",
                ai_recommendation__decision__in=["recommend", "reject"],
            )
            .count()
        )

        if new_opportunities_count == 0:
            return []

        if new_opportunities_count == 1:
            message = (
                "1 nouvelle opportunité détectée "
                "depuis votre dernière visite."
            )
        else:
            message = (
                f"{new_opportunities_count} nouvelles opportunités "
                "détectées depuis votre dernière visite."
            )

        return [
            {
                "icon": "✨",
                "message": message,
            }
        ]

        
        