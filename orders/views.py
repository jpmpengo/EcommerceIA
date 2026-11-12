import secrets
from datetime import timedelta

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import get_connection, send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from cart.cart import Cart
from dashboard.services.access_service import DashboardAccessService
from products.models import Product

from .forms import OrderCreateForm
from .models import Order, SupplierOrder, OrderProcessingEvent, CustomerSatisfaction
from .services.supplier_order_sandbox_runner import SupplierOrderSandboxRunner
from .services.payment_service import OrderPaymentService
from .services.reservation_service import OrderReservationService
from .services.supplier_preparation_runner import SupplierPreparationRunner
from .services.supplier_order_submission_runner import SupplierOrderSubmissionRunner


def _get_accessible_order(request, order_id):
    orders = Order.objects.prefetch_related("items__product", "supplier_orders")

    if request.user.is_authenticated:
        return get_object_or_404(
            orders,
            id=order_id,
            user=request.user,
        )

    guest_order_ids = request.session.get("guest_order_ids", [])
    recovered_order_ids = request.session.get("recovered_order_ids", [])

    if order_id in recovered_order_ids:
        return get_object_or_404(orders, id=order_id)

    if order_id in guest_order_ids:
        return get_object_or_404(orders, id=order_id, user__isnull=True)

    raise Http404("Cette commande n'est pas accessible.")


def order_recovery(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        try:
            validate_email(email)
        except ValidationError:
            return render(
                request,
                "orders/order_recovery.html",
                {
                    "email": email,
                    "error": "Saisissez une adresse e-mail valide.",
                },
                status=400,
            )

        code = f"{secrets.randbelow(1000000):06d}"

        requested_order_id = request.POST.get("order_id") or request.GET.get("order_id") or ""
        request.session["order_recovery"] = {
            "order_id": int(requested_order_id) if requested_order_id.isdecimal() else None,
            "email": email,
            "code_hash": make_password(code),
            "expires_at": (
                timezone.now() + timedelta(minutes=10)
            ).isoformat(),
            "attempts": 0,
        }

        if Order.objects.filter(email__iexact=email).exists():
            send_mail(
                subject="Votre code EcommerceIA",
                message=(
                    "Votre code pour retrouver vos commandes est : "
                    f"{code}\n\n"
                    "Ce code est valable pendant 10 minutes."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                connection=get_connection(
                    backend=getattr(settings, 'ORDER_RECOVERY_EMAIL_BACKEND', settings.EMAIL_BACKEND)
                ),
            )

        return redirect("orders:order_recovery_verify")

    return render(request, "orders/order_recovery.html")


def order_recovery_verify(request):
    recovery = request.session.get("order_recovery")

    if not recovery:
        return redirect("orders:order_recovery")

    email = recovery.get("email", "")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        expires_at = parse_datetime(recovery.get("expires_at", ""))

        if expires_at is None or timezone.now() >= expires_at:
            request.session.pop("order_recovery", None)
            messages.error(
                request,
                "Ce code a expiré. Demandez un nouveau code.",
            )
            return redirect("orders:order_recovery")

        attempts = int(recovery.get("attempts", 0))
        code_is_valid = (
            len(code) == 6
            and code.isdigit()
            and check_password(code, recovery.get("code_hash", ""))
        )

        if not code_is_valid:
            attempts += 1

            if attempts >= 5:
                request.session.pop("order_recovery", None)
                messages.error(
                    request,
                    "Trop de tentatives. Demandez un nouveau code.",
                )
                return redirect("orders:order_recovery")

            recovery["attempts"] = attempts
            request.session["order_recovery"] = recovery

            return render(
                request,
                "orders/order_recovery_verify.html",
                {
                    "email": email,
                    "error": "Le code saisi est incorrect.",
                },
                status=400,
            )

        recovered_order_ids = list(
            Order.objects.filter(
                email__iexact=email,
            ).values_list("id", flat=True)
        )

        request.session["recovered_order_ids"] = recovered_order_ids
        request.session.pop("order_recovery", None)

        requested_order_id = recovery.get("order_id")
        if requested_order_id in recovered_order_ids:
            return redirect("orders:order_detail", order_id=requested_order_id)
        return redirect("orders:order_list")

    return render(
        request,
        "orders/order_recovery_verify.html",
        {"email": email},
    )


def order_create(request):
    cart = Cart(request)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            cart_items = list(cart)

            if not cart_items:
                messages.warning(request, "Votre panier est vide.")
                return redirect("cart:cart_detail")

            try:
                with transaction.atomic():
                    locked_products = {}

                    for item in cart_items:
                        product = (
                            Product.objects.select_for_update().get(
                                id=item["product"].id
                            )
                        )
                        locked_products[product.id] = product

                        if (
                            not product.is_available
                            or item["quantity"] > product.stock
                        ):
                            raise ValueError(
                                f"Le produit « {product.name} » "
                                "n'a plus assez de stock."
                            )

                    order = form.save(commit=False)

                    if order.billing_same_as_shipping:
                        order.billing_first_name = order.first_name
                        order.billing_last_name = order.last_name
                        order.billing_address = order.address
                        order.billing_postal_code = order.postal_code
                        order.billing_city = order.city
                        order.billing_country = order.country

                    if request.user.is_authenticated:
                        order.user = request.user

                    order.save()
                    order.set_reservation_expiration()
                    order.save(update_fields=["reservation_expires_at"])

                    for item in cart_items:
                        product = locked_products[item["product"].id]
                        OrderReservationService.reserve(
                            order=order,
                            product=product,
                            quantity=item["quantity"],
                        )

            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect("cart:cart_detail")

            cart.clear()

            if not request.user.is_authenticated:
                guest_order_ids = request.session.get(
                    "guest_order_ids",
                    [],
                )

                if order.id not in guest_order_ids:
                    guest_order_ids.append(order.id)

                request.session["guest_order_ids"] = guest_order_ids
                request.session.modified = True

            return redirect("orders:order_created", order_id=order.id)

    else:
        form = OrderCreateForm()

    return render(
        request,
        "orders/order_create.html",
        {
            "cart": cart,
            "form": form,
        },
    )


def order_created(request, order_id):
    order = _get_accessible_order(request, order_id)
    order = OrderReservationService.expire_order(order)

    return render(
        request,
        "orders/order_created.html",
        {"order": order},
    )


def payment_create(request, order_id):
    order = _get_accessible_order(request, order_id)

    if order.paid:
        raise Http404("Cette commande est déjà payée.")

    if order.reservation_has_expired():
        order.status = "expired"
        order.save(update_fields=["status"])
        messages.error(
            request,
            "La réservation de cette commande a expiré. "
            "Le paiement n'est plus disponible.",
        )
        return redirect("orders:order_detail", order_id=order.id)

    if order.status != "pending":
        messages.error(
            request,
            "Cette commande ne peut plus être payée.",
        )
        return redirect("orders:order_detail", order_id=order.id)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = []

    for item in order.items.all():
        line_items.append(
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": item.product.name},
                    "unit_amount": int(item.price * 100),
                },
                "quantity": item.quantity,
            }
        )

    success_url = request.build_absolute_uri(
        reverse("orders:payment_success")
    )
    success_url += "?session_id={CHECKOUT_SESSION_ID}"

    cancel_url = request.build_absolute_uri(
        reverse("orders:order_detail", args=[order.id])
    )

    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=order.email,
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(order.id),
        metadata={"order_id": str(order.id)},
    )

    order.stripe_checkout_session_id = checkout_session.id
    order.save(update_fields=["stripe_checkout_session_id"])

    return HttpResponse(
        status=303,
        headers={"Location": checkout_session.url},
    )


def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        messages.error(request, "La session de paiement est introuvable.")

        if request.user.is_authenticated:
            return redirect("orders:order_list")

        return redirect("cart:cart_detail")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    metadata = getattr(checkout_session, "metadata", {})
    order_id = getattr(metadata, "order_id", None)

    if order_id is None and isinstance(metadata, dict):
        order_id = metadata.get("order_id")

    # Compatibilité avec les sessions Stripe créées avant l'ajout
    # de metadata.order_id, notamment la commande locale nº 20.
    if order_id is None:
        order_id = getattr(
            checkout_session,
            "client_reference_id",
            None,
        )

    if order_id is None:
        raise Http404("La commande associée est introuvable.")

    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        raise Http404("L'identifiant de commande est invalide.")

    order = _get_accessible_order(request, order_id)

    if order.stripe_checkout_session_id != session_id:
        raise Http404(
            "Cette session de paiement ne correspond pas à la commande."
        )

    payment_status = getattr(checkout_session, "payment_status", None)

    if payment_status != "paid":
        messages.warning(
            request,
            "Le paiement n'est pas encore confirmé par Stripe.",
        )
        return redirect("orders:order_detail", order_id=order.id)

    order = OrderPaymentService.confirm_payment(
        order_id=order.id,
        stripe_session_id=session_id,
    )

    return render(
        request,
        "orders/payment_success.html",
        {
            "order": order,
            "checkout_session": checkout_session,
        },
    )


def order_list(request):
    orders = Order.objects.prefetch_related("items__product", "supplier_orders")

    if request.user.is_authenticated:
        orders = orders.filter(user=request.user)
    else:
        guest_order_ids = request.session.get("guest_order_ids", [])
        recovered_order_ids = request.session.get("recovered_order_ids", [])
        from django.db.models import Q
        orders = orders.filter(
            Q(id__in=guest_order_ids, user__isnull=True)
            | Q(id__in=recovered_order_ids)
        )

    OrderReservationService.expire_overdue_orders(orders)
    orders = orders.order_by("-id")

    return render(
        request,
        "orders/order_list.html",
        {"orders": orders},
    )


@require_POST
def order_confirm_receipt(request, order_id):
    order = _get_accessible_order(request, order_id)
    if order.status != "delivered":
        messages.error(request, "La livraison de cette commande n est pas encore confirmee par le transporteur.")
    elif order.reception_disputed_at is not None:
        messages.error(request, "Une contestation est en cours. Contactez le service client.")
    elif order.customer_received_at is None:
        order.customer_received_at = timezone.now()
        order.save(update_fields=["customer_received_at"])
        messages.success(request, "Votre confirmation de reception a ete enregistree.")
    else:
        messages.info(request, "Vous avez deja confirme la reception de cette commande.")
    return redirect("orders:order_detail", order_id=order.id)


@require_POST
def order_report_delivery_issue(request, order_id):
    order = _get_accessible_order(request, order_id)
    if order.status != 'delivered':
        messages.error(request, 'Cette commande n est pas encore declaree livree.')
    elif order.reception_disputed_at is None:
        order.reception_disputed_at = timezone.now()
        order.save(update_fields=['reception_disputed_at'])
        messages.success(request, 'Votre signalement a ete enregistre.')
    else:
        messages.info(request, 'Un signalement existe deja pour cette commande.')
    return redirect('orders:order_detail', order_id=order.id)

@require_POST
@transaction.atomic
def order_submit_satisfaction(request, order_id):
    order = _get_accessible_order(request, order_id)
    if order.status != "delivered" or not (order.customer_received_at or order.reception_assumed_at) or order.reception_disputed_at:
        messages.error(request, "Cette commande ne peut pas encore etre evaluee.")
        return redirect("orders:order_detail", order_id=order.id)
    rating_text = request.POST.get("rating", "").strip()
    comment = request.POST.get("comment", "").strip()
    if rating_text not in ("1", "2", "3", "4", "5"):
        messages.error(request, "Veuillez choisir une note de 1 a 5.")
        return redirect("orders:order_detail", order_id=order.id)
    satisfaction, created = CustomerSatisfaction.objects.select_for_update().get_or_create(order=order)
    if satisfaction.responded_at is not None:
        messages.info(request, "Votre avis a deja ete enregistre.")
    else:
        satisfaction.rating = int(rating_text)
        satisfaction.comment = comment
        satisfaction.responded_at = timezone.now()
        satisfaction.save(update_fields=["rating", "comment", "responded_at"])
        messages.success(request, "Merci, votre avis a ete enregistre.")
    return redirect("orders:order_detail", order_id=order.id)


def order_detail(request, order_id):
    order = _get_accessible_order(request, order_id)
    order = OrderReservationService.expire_order(order)

    return render(
        request,
        "orders/order_detail.html",
        {"order": order},
    )


def invoice_detail(request, order_id):
    order = _get_accessible_order(request, order_id)

    if not order.paid:
        raise Http404("La facture n\'est disponible qu\'après paiement.")

    try:
        invoice = order.invoice
    except Exception:
        raise Http404("Aucune facture n\'est disponible pour cette commande.")

    invoice_items = list(invoice.items.all())
    order_items = list(order.items.select_related("product").all())
    invoice_rows = [{"invoice_item": invoice_item, "order_item": order_item} for invoice_item, order_item in zip(invoice_items, order_items)]

    return render(
        request,
        "orders/invoice_detail.html",
        {
            "order": order,
            "invoice": invoice,
            "invoice_rows": invoice_rows,
        },
    )


def invoice_pdf(request, order_id):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    order = _get_accessible_order(request, order_id)
    if not order.paid:
        raise Http404("La facture n\'est disponible qu\'après paiement.")

    try:
        invoice = order.invoice
    except Exception:
        raise Http404("Aucune facture n\'est disponible pour cette commande.")

    response = HttpResponse(content_type="application/pdf")
    disposition = "inline" if request.GET.get("print") == "1" else "attachment"
    response["Content-Disposition"] = f"{disposition}; filename={invoice.number}.pdf"

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    blue = colors.HexColor("#173B7A")
    blue_text = colors.HexColor("#2459C4")
    pale_blue = colors.HexColor("#F4F8FF")
    border_blue = colors.HexColor("#E1EBFF")
    muted = colors.HexColor("#64748B")

    margin = 42
    content_width = width - (margin * 2)

    pdf.setFillColor(colors.white)
    pdf.roundRect(margin, 55, content_width, height - 110, 14, fill=1, stroke=0)

    y = height - 70
    pdf.setFillColor(blue)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin + 16, y, invoice.merchant_trade_name or invoice.merchant_legal_name)
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawRightString(width - margin - 16, y, "Facture")

    y -= 30
    pdf.setFillColor(blue_text)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(width - margin - 16, y, invoice.number)
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 9)
    y -= 14
    pdf.drawRightString(width - margin - 16, y, f"Commande #{order.id}")

    y -= 38
    gap = 14
    box_w = (content_width - gap) / 2
    box_h = 125
    left_x = margin
    right_x = margin + box_w + gap
    box_y = y - box_h

    pdf.setFillColor(pale_blue)
    pdf.setStrokeColor(border_blue)
    pdf.roundRect(left_x, box_y, box_w, box_h, 10, fill=1, stroke=1)
    pdf.roundRect(right_x, box_y, box_w, box_h, 10, fill=1, stroke=1)

    pdf.setFillColor(blue_text)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(left_x + 14, y - 22, "Vendeur")
    pdf.drawString(right_x + 14, y - 22, "Facturé à")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(left_x + 14, y - 42, invoice.merchant_legal_name)
    pdf.drawString(right_x + 14, y - 42, f"{invoice.billing_first_name} {invoice.billing_last_name}")

    pdf.setFont("Helvetica", 9)
    pdf.drawString(left_x + 14, y - 58, invoice.merchant_address)
    pdf.drawString(right_x + 14, y - 58, invoice.billing_address)
    pdf.drawString(left_x + 14, y - 74, f"{invoice.merchant_postal_code} {invoice.merchant_city}")
    pdf.drawString(right_x + 14, y - 74, f"{invoice.billing_postal_code} {invoice.billing_city}")
    pdf.drawString(left_x + 14, y - 90, invoice.merchant_country)
    pdf.drawString(right_x + 14, y - 90, invoice.billing_country)
    if invoice.merchant_siret:
        pdf.drawString(left_x + 14, y - 106, f"SIRET : {invoice.merchant_siret}")
    if invoice.merchant_vat_number:
        pdf.drawString(left_x + 14, y - 120, f"TVA : {invoice.merchant_vat_number}")

    y = box_y - 34
    pdf.setFillColor(pale_blue)
    pdf.setStrokeColor(border_blue)
    pdf.roundRect(margin, y - 24, content_width, 28, 6, fill=1, stroke=1)
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(margin + 12, y - 6, "ARTICLE")
    pdf.drawCentredString(365, y - 6, "QUANTITÉ")
    pdf.drawRightString(475, y - 6, "PRIX UNITAIRE TTC")
    pdf.drawRightString(width - margin - 12, y - 6, "TOTAL TTC")

    y -= 48
    invoice_items = list(invoice.items.all())
    order_items = list(order.items.select_related("product").all())
    for invoice_item, order_item in zip(invoice_items, order_items):
        if order_item.product.image:
            try:
                pdf.drawImage(ImageReader(order_item.product.image.path), margin + 8, y - 30, width=44, height=44, preserveAspectRatio=True, anchor="c", mask="auto")
            except Exception:
                pass
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin + 62, y - 10, invoice_item.description[:48])
        pdf.drawCentredString(365, y - 10, str(invoice_item.quantity))
        pdf.drawRightString(475, y - 10, f"{invoice_item.unit_price_ttc} EUR")
        pdf.drawRightString(width - margin - 12, y - 10, f"{invoice_item.total_ttc} EUR")
        pdf.setStrokeColor(colors.HexColor("#E5E7EB"))
        pdf.line(margin, y - 38, width - margin, y - 38)
        y -= 58

    totals_x = width - margin - 210
    y -= 6
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.black)
    pdf.drawString(totals_x, y, "Total HT")
    pdf.drawRightString(width - margin - 12, y, f"{invoice.total_ht} EUR")
    y -= 22
    pdf.drawString(totals_x, y, "TVA (20 %)")
    pdf.drawRightString(width - margin - 12, y, f"{invoice.vat_amount} EUR")

    y -= 32
    pdf.setFillColor(blue)
    pdf.roundRect(totals_x - 8, y - 12, 218, 36, 7, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(totals_x + 4, y, "Total TTC")
    pdf.drawRightString(width - margin - 20, y, f"{invoice.total_ttc} EUR")

    footer_y = 82
    pdf.setStrokeColor(colors.HexColor("#E5E7EB"))
    pdf.line(margin, footer_y + 20, width - margin, footer_y + 20)
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(margin, footer_y, f"Paiement confirmé pour la commande #{order.id}.")

    pdf.showPage()
    pdf.save()
    return response


@login_required
def operator_order_list(request):
    if not DashboardAccessService.can_access(request.user):
        return redirect("products:product_list")

    orders = (
        Order.objects
        .prefetch_related("items__product", "supplier_orders")
        .order_by("-created_at")
    )

    OrderReservationService.expire_overdue_orders(orders)

    status_filter = request.GET.get("status", "all")
    allowed_filters = {"all", "paid", "processing", "shipped", "delivered", "incidents"}
    if status_filter not in allowed_filters:
        status_filter = "all"
    if status_filter == "incidents":
        orders = orders.filter(Q(supplier_orders__status="failed") | Q(status="paid", supplier_orders__isnull=True, processing_events__event_type="supplier_preparation_failed")).distinct()
    elif status_filter != "all":
        orders = orders.filter(status=status_filter)

    preparation_failed_ids = set(OrderProcessingEvent.objects.filter(event_type="supplier_preparation_failed", order__status="paid").values_list("order_id", flat=True))
    for order in orders:
        dossiers = list(order.supplier_orders.all())
        order.incident_type = "supplier_failed" if any(d.status == "failed" for d in dossiers) else ("preparation_failed" if order.status == "paid" and not dossiers and order.id in preparation_failed_ids else None)

    dashboard_stats = {
        "total": Order.objects.count(),
        "paid": Order.objects.filter(status="paid").count(),
        "processing": Order.objects.filter(status="processing").count(),
        "shipped": Order.objects.filter(status="shipped").count(),
        "delivered": Order.objects.filter(status="delivered").count(),
        "incidents": Order.objects.filter(Q(supplier_orders__status="failed") | Q(status="paid", supplier_orders__isnull=True, processing_events__event_type="supplier_preparation_failed")).distinct().count(),
    }

    from decimal import Decimal
    from datetime import date
    from django.utils import timezone
    from django.utils.timezone import localdate
    today = localdate()
    days = [today - timedelta(days=i) for i in range(29, -1, -1)]
    daily = {day: {"orders": 0, "revenue": Decimal("0.00")} for day in days}
    for chart_order in Order.objects.prefetch_related("items").filter(created_at__date__gte=days[0], created_at__date__lte=today):
        day = timezone.localtime(chart_order.created_at).date()
        if day in daily:
            daily[day]["orders"] += 1
            if chart_order.paid:
                daily[day]["revenue"] += chart_order.get_total_price()
    order_chart_data = [{"date": day.strftime("%d/%m"), "orders": daily[day]["orders"], "revenue": float(daily[day]["revenue"])} for day in days]

    shipment_overview = list(
        SupplierOrder.objects.select_related("order", "supplier")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "orders/operator_order_list.html",
        {
            "orders": orders,
            "operator_view": True,
            "dashboard_stats": dashboard_stats,
            "order_chart_data": order_chart_data,
            "shipment_overview": shipment_overview,
            "status_filter": status_filter,
        },
    )


@login_required
@require_POST
def operator_submit_supplier_order(request, order_id):
    if not DashboardAccessService.can_access(request.user):
        return redirect("products:product_list")

    order = get_object_or_404(Order, id=order_id)

    try:
        SupplierOrderSubmissionRunner.run(
            order,
            sandbox=True,
            retry_failed=False,
            source="manual",
        )
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            "Commande fournisseur transmise en sandbox.",
        )

    return redirect(
        "orders:operator_order_detail",
        order_id=order.id,
    )


@login_required
@require_POST
def operator_prepare_supplier_order(request, order_id):
    if not DashboardAccessService.can_access(request.user):
        return redirect("products:product_list")

    order = get_object_or_404(Order, id=order_id)

    try:
        SupplierPreparationRunner.run(
            order,
            source="manual",
        )
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(
            request,
            "Préparation fournisseur effectuée.",
        )

    return redirect(
        "orders:operator_order_detail",
        order_id=order.id,
    )


@login_required
@require_POST
def operator_sync_supplier_order(request, order_id, supplier_order_id):
    if not DashboardAccessService.can_access(request.user):
        return redirect("products:product_list")
    supplier_order = get_object_or_404(SupplierOrder, id=supplier_order_id, order_id=order_id)
    try:
        SupplierOrderSandboxRunner.run(supplier_order, "sync")
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Commande fournisseur synchronisee avec CJ sandbox.")
    return redirect("orders:operator_order_detail", order_id=order_id)


@login_required
def operator_order_detail(request, order_id):
    if not DashboardAccessService.can_access(request.user):
        return redirect("products:product_list")

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product", "supplier_orders", "processing_events"),
        id=order_id,
    )
    order = OrderReservationService.expire_order(order)

    items = list(order.items.all())
    can_prepare_supplier_order = (
        order.paid
        and bool(items)
        and not order.supplier_orders.exists()
        and all(
            getattr(getattr(item.product, "source_opportunity", None), "supplier_offer", None)
            and getattr(item.product.source_opportunity.supplier_offer, "supplier_verified_at", None)
            and item.product.source_opportunity.supplier_offer.shipping_country == order.country
            for item in items
        )
        and any(not hasattr(item, "supplier_preparation") for item in items)
    )

    can_submit_supplier_order = (
        order.paid
        and order.status == "paid"
        and bool(items)
        and all(hasattr(item, "supplier_preparation") for item in items)
        and not order.supplier_orders.filter(status="submitted").exists()
    )

    return render(
        request,
        "orders/operator_order_detail.html",
        {
            "order": order,
            "operator_view": True,
            "can_prepare_supplier_order": can_prepare_supplier_order,
            "can_submit_supplier_order": can_submit_supplier_order,
        },
    )


@csrf_exempt
def stripe_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        order_id = metadata.get("order_id")

        if order_id:
            order = Order.objects.filter(
                id=order_id,
                paid=False,
            ).first()

            if order is not None:
                OrderPaymentService.confirm_payment(
                    order_id=order_id,
                    stripe_session_id=session["id"],
                )

    return HttpResponse(status=200)


def order_cancel(request, order_id):
    order = _get_accessible_order(request, order_id)

    if request.method != "POST":
        return redirect("orders:order_detail", order_id=order.id)

    if order.status == "pending" and not order.paid:
        order.status = "cancelled"
        order.save(update_fields=["status"])
        messages.success(request, "Votre commande a été annulée.")

    return redirect("orders:order_detail", order_id=order.id)

def satisfaction_from_email(request, token):
    from django.core import signing
    try:
        data = signing.loads(token, salt='ecommerceia-satisfaction', max_age=2592000)
        order_id = data['order_id']
    except (signing.BadSignature, ValueError, TypeError, KeyError):
        raise Http404('Lien de satisfaction invalide ou expire.')
    order = get_object_or_404(Order, pk=order_id)
    if order.status != 'delivered' or not (order.customer_received_at or order.reception_assumed_at) or order.reception_disputed_at:
        raise Http404('Enquete indisponible.')
    satisfaction = CustomerSatisfaction.objects.filter(order=order, request_sent_at__isnull=False).first()
    if satisfaction is None:
        raise Http404('Invitation indisponible.')
    if satisfaction.responded_at:
        return HttpResponse('Merci, votre avis a deja ete enregistre.')
    selected_rating = request.GET.get('rating', '')
    if request.method == 'POST':
        rating = request.POST.get('rating', '')
        if rating not in ('1','2','3','4','5'):
            return HttpResponse('Veuillez choisir une note de 1 a 5.', status=400)
        with transaction.atomic():
            satisfaction = CustomerSatisfaction.objects.select_for_update().get(pk=satisfaction.pk)
            if satisfaction.responded_at:
                return HttpResponse('Votre avis a deja ete enregistre.')
            satisfaction.rating = int(rating)
            satisfaction.comment = request.POST.get('comment', '').strip()
            satisfaction.responded_at = timezone.now()
            satisfaction.save(update_fields=['rating', 'comment', 'responded_at'])
        return HttpResponse('Merci pour votre avis !')
    product = next((item.product for item in order.items.select_related('product').all()), None)
    return render(request, 'orders/satisfaction_form.html', {'order': order, 'product': product, 'notes': range(1, 6), 'selected_rating': int(selected_rating) if selected_rating in ('1','2','3','4','5') else 0})

