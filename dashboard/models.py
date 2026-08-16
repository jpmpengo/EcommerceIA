from django.conf import settings
from django.db import models


class EmmaMemory(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emma_memory",
        verbose_name="Commerçant",
    )

    last_visit = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière visite",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Mise à jour le",
    )

    def __str__(self):
        return f"Mémoire Emma — {self.user}"

        

