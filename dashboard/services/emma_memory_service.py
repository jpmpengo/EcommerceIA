from django.utils import timezone

from dashboard.models import EmmaMemory


class EmmaMemoryService:
    """
    Gère la mémoire des interactions entre Emma
    et le commerçant.
    """

    @staticmethod
    def get(user):
        memory, _ = EmmaMemory.objects.get_or_create(
            user=user,
        )
        return memory

    @staticmethod
    def last_visit(user):
        memory = EmmaMemoryService.get(user)
        return memory.last_visit

    @staticmethod
    def record_visit(user):
        memory = EmmaMemoryService.get(user)
        previous_visit = memory.last_visit

        memory.last_visit = timezone.now()
        memory.save(
            update_fields=[
                "last_visit",
                "updated_at",
            ]
        )

        return previous_visit
        