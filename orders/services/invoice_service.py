from decimal import Decimal, ROUND_HALF_UP

from orders.models import Invoice, InvoiceItem, MerchantLegalEntity, OrderProcessingEvent


class InvoiceService:
    @staticmethod
    def create_for_paid_order(order):
        if not order.paid:
            raise ValueError("Une facture ne peut être créée que pour une commande payée.")

        existing = Invoice.objects.filter(order=order).first()
        if existing:
            return existing

        merchant = MerchantLegalEntity.get_active()
        total_ttc = sum(
            (item.get_cost() for item in order.items.all()),
            Decimal("0.00"),
        )
        vat_rate = Decimal("0.20")
        total_ht = (
            total_ttc / (Decimal("1.00") + vat_rate)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vat_amount = (total_ttc - total_ht).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        invoice = Invoice.objects.create(
            order=order,
            merchant=merchant,
            number=f"FAC-{order.id:06d}",
            merchant_legal_name=merchant.legal_name,
            merchant_trade_name=merchant.trade_name,
            merchant_siren=merchant.siren,
            merchant_siret=merchant.siret,
            merchant_vat_number=merchant.vat_number,
            merchant_address=merchant.address,
            merchant_postal_code=merchant.postal_code,
            merchant_city=merchant.city,
            merchant_country=merchant.country,
            billing_first_name=order.billing_first_name,
            billing_last_name=order.billing_last_name,
            billing_address=order.billing_address,
            billing_postal_code=order.billing_postal_code,
            billing_city=order.billing_city,
            billing_country=order.billing_country,
            total_ttc=total_ttc,
            vat_rate=vat_rate,
            total_ht=total_ht,
            vat_amount=vat_amount,
        )

        for item in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                description=item.product.name,
                image_url=item.product.image.url if item.product.image else "",
                quantity=item.quantity,
                unit_price_ttc=item.price,
                total_ttc=item.get_cost(),
            )

        OrderProcessingEvent.objects.create(
            order=order,
            event_type="invoice_created",
            source="automatic",
        )

        return invoice
