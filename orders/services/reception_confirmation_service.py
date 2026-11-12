from datetime import timedelta
from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone


class ReceptionConfirmationService:
    @staticmethod
    def build_message(order, site_url):
        recovery_url = site_url.rstrip(chr(47)) + reverse('orders:order_recovery') + '?order_id=' + str(order.id)
        subject = 'EcommerceIA - Confirmation de reception de votre commande'
        message = (
            'Bonjour,\n\n'
            + 'Le transporteur indique que votre commande n°' + str(order.id) + ' a ete livree.\n\n'
            + 'Pour confirmer sa reception ou signaler un probleme, retrouvez vos commandes ici :\n' + recovery_url
            + '\n\nSans confirmation ni reclamation sous 7 jours calendaires apres la livraison constatee, la reception pourra etre consideree comme presumee.\n'
            + '\nCette presomption ne supprime pas vos droits.\n\nEcommerceIA'
        )
        return subject, message

    @staticmethod
    def should_send(order):
        return (
            order.status == 'delivered'
            and order.delivered_at is not None
            and order.reception_request_sent_at is None
            and order.customer_received_at is None
            and order.reception_disputed_at is None
        )

    @staticmethod
    def can_assume_reception(order, now=None):
        now = now or timezone.now()
        return (
            order.status == "delivered"
            and order.delivered_at is not None
            and order.delivered_at <= now - timedelta(days=7)
            and order.reception_request_sent_at is not None
            and order.reception_request_sent_at <= now
            and order.customer_received_at is None
            and order.reception_disputed_at is None
            and order.reception_assumed_at is None
        )

    @staticmethod
    def assume_reception(order_id):
        from orders.models import Order
        now = timezone.now()
        updated = Order.objects.filter(
            pk=order_id,
            status="delivered",
            delivered_at__isnull=False,
            delivered_at__lte=now - timedelta(days=7),
            reception_request_sent_at__isnull=False,
            reception_request_sent_at__lte=now,
            customer_received_at__isnull=True,
            reception_disputed_at__isnull=True,
            reception_assumed_at__isnull=True,
        ).update(reception_assumed_at=now)
        return updated == 1

    @staticmethod
    def claim_request(order_id):
        from orders.models import Order
        now = timezone.now()
        updated = (
            Order.objects.filter(
                pk=order_id,
                status='delivered',
                delivered_at__isnull=False,
                reception_request_sent_at__isnull=True,
                customer_received_at__isnull=True,
                reception_disputed_at__isnull=True,
                reception_assumed_at__isnull=True,
            )
            .filter(reception_request_claimed_at__isnull=True)
            .update(reception_request_claimed_at=now)
        )
        return updated == 1

    @staticmethod
    def send_request(order_id, site_url):
        from orders.models import Order
        if not ReceptionConfirmationService.claim_request(order_id):
            return False
        order = Order.objects.get(pk=order_id)
        subject, message = ReceptionConfirmationService.build_message(order, site_url)
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ORDER_RECEPTION_TEST_EMAIL],
            fail_silently=False,
            connection=get_connection(backend=settings.ORDER_RECOVERY_EMAIL_BACKEND),
        )
        if sent_count != 1:
            raise RuntimeError('Envoi email non confirme')
        Order.objects.filter(pk=order_id, reception_request_sent_at__isnull=True).update(reception_request_sent_at=timezone.now())
        return True
