import ssl
from decimal import Decimal

import httpx
import truststore

from orders.services.customs_duty_service import (
    CustomsDutyService,
)
from product_intelligence.services.currency_conversion import (
    CurrencyConversionService,
)
from product_intelligence.services.exchange_rate_client import (
    ExchangeRateClient,
)
from product_intelligence.services.opportunity_cost_calculation import (
    OpportunityCostCalculationService,
)
from product_intelligence.services.minimum_profitable_price import (
    MinimumProfitablePriceService,
)
from product_intelligence.services.supplier_offer_analysis_pipeline import (
    SupplierOfferAnalysisPipeline,
)
from product_intelligence.services.supplier_offer_base_cost import (
    SupplierOfferBaseCostService,
)
from product_intelligence.services.supplier_offer_evaluation import (
    SupplierOfferEvaluationService,
)
from product_intelligence.services.supplier_offer_opportunity import (
    SupplierOfferOpportunityService,
)


class SupplierOfferAnalysisRunner:
    """Construit et exécute l'analyse financière d'une offre."""

    def __init__(
        self,
        market_currency="EUR",
        minimum_profit=Decimal("0.01"),
        minimum_margin_rate=Decimal("10.00"),
        vat_rate=Decimal("0.20"),
        payment_rate=Decimal("0.015"),
        payment_fixed_fee=Decimal("0.25"),
        return_reserve_rate=Decimal("0.05"),
        safety_reserve_rate=Decimal("0.05"),
    ):
        self.market_currency = market_currency
        self.minimum_profit = minimum_profit
        self.minimum_margin_rate = minimum_margin_rate
        self.vat_rate = vat_rate
        self.payment_rate = payment_rate
        self.payment_fixed_fee = payment_fixed_fee
        self.return_reserve_rate = return_reserve_rate
        self.safety_reserve_rate = safety_reserve_rate

    def process(self, supplier_offer, create=False):
        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        with httpx.Client(
            verify=ssl_context,
            timeout=20.0,
        ) as http_client:
            cost_calculation_service = OpportunityCostCalculationService(
                vat_rate=self.vat_rate,
                import_duty_rate=Decimal("0"),
                payment_rate=self.payment_rate,
                payment_fixed_fee=self.payment_fixed_fee,
                return_reserve_rate=self.return_reserve_rate,
                safety_reserve_rate=self.safety_reserve_rate,
            )

            pipeline = SupplierOfferAnalysisPipeline(
                evaluation_service=(
                    SupplierOfferEvaluationService(
                        price_policy="minimum"
                    )
                ),
                base_cost_service=(
                    SupplierOfferBaseCostService(
                        rate_client=(
                            ExchangeRateClient(
                                http_client
                            )
                        ),
                        conversion_service=(
                            CurrencyConversionService()
                        ),
                    )
                ),
                cost_calculation_service=cost_calculation_service,
                opportunity_service=(
                    SupplierOfferOpportunityService()
                ),
                customs_duty_service=CustomsDutyService(),
                minimum_profitable_price_service=(
                    MinimumProfitablePriceService(
                        cost_calculation_service=cost_calculation_service,
                    )
                ),
                minimum_projected_profit=(
                    self.minimum_profit
                ),
                minimum_margin_rate=(
                    self.minimum_margin_rate
                ),
            )

            return pipeline.process(
                supplier_offer=supplier_offer,
                market_currency=self.market_currency,
                create=create,
            )
