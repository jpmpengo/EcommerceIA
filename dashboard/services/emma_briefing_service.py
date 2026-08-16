from orders.models import Order
from products.models import Product
from product_intelligence.models import ProductOpportunity

from dashboard.services.emma_changes_service import (
    EmmaChangesService,
)
from dashboard.services.emma_memory_service import (
    EmmaMemoryService,
)
from dashboard.services.priority_advisor import (
    PriorityAdvisor,
)
from dashboard.services.emma_attention_service import (
    EmmaAttentionService,
)
from dashboard.services.emma_progress_service import (
    EmmaProgressService,
)
from dashboard.services.emma_state_service import (
    EmmaStateService,
)
from dashboard.services.emma_summary_service import (
    EmmaSummaryService,
)

from dashboard.services.emma_preparation_service import (
    EmmaPreparationService,
)

from dashboard.models import EmmaMemory
from django.utils import timezone

from dashboard.services.emma_restock_service import (
    EmmaRestockService,
)


class EmmaBriefingService:
    """
    Prépare le briefing présenté par Emma
    au commerçant.
    """

    @staticmethod
    def build(user):
        previous_visit = EmmaMemoryService.record_visit(
            user
        )

        progress = EmmaProgressService.get_progress(
            previous_visit
        )

        priority = PriorityAdvisor.get_priority()

        alerts = EmmaAttentionService.get_alerts(
            priority
        )

        changes = EmmaBriefingService._build_changes(
            previous_visit
        )

        preparation = EmmaPreparationService.get_items()

        restock = EmmaRestockService.get_items()

        state = EmmaStateService.get_state(
            progress,
            priority,
            alerts,
            preparation,
        )

        summary = EmmaSummaryService.build(
            state
        )

        return {
            "greeting": (
                EmmaBriefingService._build_greeting(
                    previous_visit
                )
            ),
            "summary": summary,
            "progress": progress,
            "priorite": priority,
            "alerts": alerts,
            "changes": changes,
            "preparation": preparation,
            "next_actions": [],
            "activity": (
                EmmaBriefingService._build_activity()
            ),
            "restock": restock,
        }

    @staticmethod
    def _build_greeting(previous_visit):
        today = timezone.localdate()

        if previous_visit is None:
            return {
                "title": "Bonjour",
                "message": "J’ai préparé votre journée.",
                "previous_visit": None,
            }

        previous_visit_date = timezone.localtime(
            previous_visit
        ).date()

        if previous_visit_date < today:
            title = "Bonjour"
            message = "Voici ce qui mérite votre attention aujourd’hui."
        else:
            title = "Bon retour"
            message = "Voici ce qui mérite maintenant votre attention."

        return {
            "title": title,
            "message": message,
            "previous_visit": previous_visit,
        }

    @staticmethod
    def _build_changes(previous_visit):
        changes = EmmaChangesService.get_changes(
            previous_visit
        )

        if changes:
            return changes

        return [
            {
                "icon": "✨",
                "message": (
                    "Aucune nouveauté depuis "
                    "votre dernière visite."
                ),
            }
        ]

    @staticmethod
    def _build_activity():
        return {
            "products": Product.objects.count(),
            "orders": Order.objects.count(),
            "opportunities": (
                ProductOpportunity.objects.count()
            ),
        }

           

