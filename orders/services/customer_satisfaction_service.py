from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from orders.models import Order, CustomerSatisfaction


class CustomerSatisfactionService:
    @staticmethod
    def send_request(order_id, site_url):
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order_id)
            if order.status != "delivered" or not (order.customer_received_at or order.reception_assumed_at) or order.reception_disputed_at:
                return False
            satisfaction, created = CustomerSatisfaction.objects.get_or_create(order=order)
            if satisfaction.request_claimed_at or satisfaction.request_sent_at or satisfaction.responded_at:
                return False
            satisfaction.request_claimed_at = timezone.now()
            satisfaction.save(update_fields=["request_claimed_at"])
        from django.core import signing
        token = signing.dumps({"order_id": order.id}, salt="ecommerceia-satisfaction")
        url = site_url.rstrip("/") + reverse("orders:satisfaction_from_email", args=[token])
        subject = "EcommerceIA - Votre avis sur votre commande"
        message = 'Bonjour,\n\nVotre commande n.{} a ete receptionnee.\n\nDonnez votre avis sur votre achat :\n{}\n\nVous pourrez attribuer une note de 1 a 5 etoiles et laisser un commentaire facultatif.\n\nCette enquete est facultative. Aucune relance ne sera envoyee.\n\nEcommerceIA'.format(order.id, url)
        from django.utils.html import escape
        html_links = '<p><a href=' + chr(34) + escape(url) + chr(34) + ' style=background-color:#3769BD;color:white;padding:14px;text-decoration:none;border-radius:6px;>Donner mon avis</a></p>'
        html_message = '<html><body><p>Bonjour,</p><p>Votre commande a ete receptionnee.</p><p>Comment evaluez-vous votre achat ?</p>{}<p>Cliquez sur le bouton pour noter votre achat et laisser, si vous le souhaitez, un commentaire.</p><p>Cette enquete est facultative. Aucune relance ne sera envoyee.</p><p>EcommerceIA</p></body></html>'.format(html_links)
        sent = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.ORDER_RECEPTION_TEST_EMAIL], fail_silently=False, connection=get_connection(backend=settings.ORDER_RECOVERY_EMAIL_BACKEND), html_message=html_message)
        if sent != 1:
            CustomerSatisfaction.objects.filter(order_id=order_id, request_sent_at__isnull=True).update(request_claimed_at=None)
            raise RuntimeError("Envoi enquete non confirme")
        CustomerSatisfaction.objects.filter(order_id=order_id, request_sent_at__isnull=True).update(request_sent_at=timezone.now())
        return True
