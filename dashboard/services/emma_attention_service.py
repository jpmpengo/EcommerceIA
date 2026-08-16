from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from product_intelligence.models import ProductOpportunity

from datetime import timedelta

from django.utils import timezone


class EmmaAttentionService:

    @staticmethod
    def get_alerts(priority):
        if priority is None:
            return []

        opportunity = priority["opportunity"]

        if opportunity.published_product is not None:
            return []

        if (
            opportunity.postponed_until
            and opportunity.postponed_until > timezone.now()
        ):
            return []

        if opportunity.detected_at > (
            timezone.now() - timedelta(days=7)
        ):
            return []

        return [
            {
                "icon": "⏳",
                "title": opportunity.name,
                "message": (
                    "Cette recommandation attend "
                    "votre décision depuis plus d'une semaine."
                ),
                "action_label": priority["action_label"],
                "action_url": priority["action_url"],
            }
        ]



        