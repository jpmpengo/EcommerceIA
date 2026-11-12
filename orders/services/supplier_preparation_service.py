from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from orders.models import OrderProcessingEvent, SupplierPreparation


class SupplierPreparationService:
    MONEY = Decimal("0.01")

    def __init__(self, base_cost_service, cost_calculation_service, customs_duty_service):
        self.base_cost_service = base_cost_service
        self.cost_calculation_service = cost_calculation_service
        self.customs_duty_service = customs_duty_service

    @transaction.atomic
    def prepare(self, order_item, target_currency="EUR", source="automatic"):
        order = order_item.order
        if not order.paid or order.status not in {
            "paid", "processing", "shipped", "delivered"
        }:
            raise ValueError("La commande doit être payée.")
        if not order.country:
            raise ValueError("Le pays de livraison est manquant.")

        opportunity = getattr(order_item.product, "source_opportunity", None)
        offer = getattr(opportunity, "supplier_offer", None)
        if offer is None:
            raise ValueError("L'offre fournisseur est introuvable.")
        if offer.supplier_verified_at is None:
            raise ValueError("L'offre fournisseur n'est pas vérifiée.")
        if offer.shipping_country != order.country:
            raise ValueError("Le pays du transport diffère du pays client.")

        base = self.base_cost_service.calculate(offer, target_currency)
        quantity = Decimal(order_item.quantity)
        purchase_original = self._money(base["purchase_original"] * quantity)
        shipping_original = self._money(base["shipping_original"] * quantity)
        purchase_converted = self._money(base["purchase_converted"] * quantity)
        shipping_converted = self._money(base["shipping_converted"] * quantity)
        base_cost = self._money(base["base_cost"] * quantity)
        customs = self.customs_duty_service.estimate(
            origin_country=offer.supplier.country,
            destination_country=order.country,
            intrinsic_value=purchase_converted,
            quantity=order_item.quantity,
        )
        import_duty = customs["amount"]
        landed_cost = self._money(base_cost + import_duty)
        sale_ttc = self._money(order_item.price * quantity)
        profitability = self.cost_calculation_service.calculate(
            decision_price=sale_ttc,
            base_cost=base_cost,
            currency=target_currency,
            import_duty=import_duty,
        )

        preparation, created = SupplierPreparation.objects.update_or_create(
            order_item=order_item,
            defaults={
                "supplier_offer": offer,
                "mode": "simulation",
                "destination_country": order.country,
                "quantity": order_item.quantity,
                "source_currency": base["source_currency"],
                "target_currency": base["target_currency"],
                "exchange_rate": base["exchange_rate"],
                "purchase_original": purchase_original,
                "shipping_original": shipping_original,
                "purchase_converted": purchase_converted,
                "shipping_converted": shipping_converted,
                "base_cost": base_cost,
                "import_duty_rate": Decimal("0"),
                "import_duty": import_duty,
                "import_duty_method": customs["method"],
                "import_duty_unit_amount": customs["unit_amount"],
                "import_duty_rule_date": customs["rule_date"],
                "customs_rule_source": customs["source_url"],
                "customs_clearance_fee": None,
                "ioss_status": "unverified",
                "landed_cost": landed_cost,
                "sale_ttc": sale_ttc,
                "vat_rate": self.cost_calculation_service.vat_rate,
                "vat_amount": profitability["vat_amount"],
                "net_revenue": profitability["net_revenue"],
                "payment_fee": profitability["payment_fee"],
                "return_reserve": profitability["return_reserve"],
                "safety_reserve": profitability["safety_reserve"],
                "total_costs": profitability["total_costs"],
                "projected_profit": profitability["projected_profit"],
                "projected_margin_rate": profitability["projected_margin_rate"],
                "rate_source": base["rate_source"],
                "supplier_verified_at": offer.supplier_verified_at,
                "calculated_at": timezone.now(),
            },
        )
        if created:
            OrderProcessingEvent.objects.create(
                order=order,
                event_type="supplier_preparation_created",
                source=source,
            )
        return preparation

    @classmethod
    def _money(cls, value):
        return value.quantize(cls.MONEY, rounding=ROUND_HALF_UP)
