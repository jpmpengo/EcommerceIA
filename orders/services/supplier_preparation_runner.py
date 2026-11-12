import ssl
from decimal import Decimal

from django.core.management import call_command

import httpx
import truststore

from orders.services.customs_duty_service import CustomsDutyService
from orders.models import SupplierPreparation
from orders.services.supplier_preparation_service import SupplierPreparationService
from product_intelligence.services.currency_conversion import CurrencyConversionService
from product_intelligence.services.exchange_rate_client import ExchangeRateClient
from product_intelligence.services.opportunity_cost_calculation import OpportunityCostCalculationService
from product_intelligence.services.supplier_offer_base_cost import SupplierOfferBaseCostService


class SupplierPreparationRunner:

    @classmethod
    def run(cls, order, source="automatic", vat_rate=Decimal("0.20")):
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        with httpx.Client(verify=context, timeout=20.0) as http_client:
            base_service = SupplierOfferBaseCostService(
                ExchangeRateClient(http_client),
                CurrencyConversionService(),
            )
            service = SupplierPreparationService(
                base_service,
                OpportunityCostCalculationService(
                    vat_rate=Decimal(vat_rate),
                    import_duty_rate=Decimal("0"),
                    payment_rate=Decimal("0.015"),
                    payment_fixed_fee=Decimal("0.25"),
                    return_reserve_rate=Decimal("0.05"),
                    safety_reserve_rate=Decimal("0.05"),
                ),
                CustomsDutyService(),
            )

            results = []
            for item in order.items.all():
                if SupplierPreparation.objects.filter(order_item=item).exists():
                    continue
                try:
                    opportunity = getattr(item.product, "source_opportunity", None)
                    offer = getattr(opportunity, "supplier_offer", None)
                    if offer is not None and offer.supplier_verified_at is None:
                        call_command("verify_cj_supplier_offer", offer.id)
                        offer.refresh_from_db()
                    results.append(service.prepare(item, source=source))
                except Exception as error:
                    print("Commande", order.id, "- article", item.id, "- erreur de preparation:", error)
            return results
