from django.core.management.base import BaseCommand

from orders.services.reservation_service import (
    OrderReservationService,
)


class Command(BaseCommand):
    help = (
        "Expire les commandes dont la réservation "
        "de stock est arrivée à échéance."
    )

    def handle(self, *args, **options):
        OrderReservationService.expire_pending_orders()

        self.stdout.write(
            self.style.SUCCESS(
                "Les commandes expirées ont été traitées."
            )
        )

        