from product_intelligence.services.comparable_price_summary import (
    ComparablePriceSummaryService,
)
from product_intelligence.services.market_price_reference import (
    MarketPriceReferenceService,
)
from product_intelligence.services.supplier_delivery_policy import (
    SupplierDeliveryPolicyService,
)


class SupplierOfferEvaluationService:

    MINIMUM_COMPARABLE_PRICES = 3
    MINIMUM_SOURCE_DOMAINS = 2

    def __init__(
        self,
        summary_service=None,
        reference_service=None,
        delivery_policy=None,
        price_policy=None,
    ):
        self.summary_service = (
            summary_service
            or ComparablePriceSummaryService
        )

        self.reference_service = (
            reference_service
            or MarketPriceReferenceService
        )

        self.delivery_policy = (
            delivery_policy
            or SupplierDeliveryPolicyService()
        )

        self.price_policy = (
            price_policy
            or self.reference_service.DEFAULT_POLICY
        )

    def prepare(
        self,
        supplier_offer,
        market_currency,
    ):
        market_summary = (
            self.summary_service.summarize(
                supplier_offer=supplier_offer,
                currency=market_currency,
            )
        )

        delivery_result = (
            self.delivery_policy.evaluate(
                shipping_days=(
                    supplier_offer.shipping_days
                ),
            )
        )

        delivery_status = (
            delivery_result["status"]
        )

        if delivery_status == "rejected":
            return self._build_dossier(
                supplier_offer=supplier_offer,
                market_summary=market_summary,
                decision_price=None,
                status="rejected",
                blockers=[
                    delivery_result["reason"],
                ],
                warnings=[],
                delivery_result=(
                    delivery_result
                ),
            )

        blockers = []
        warnings = []

        if (
            market_summary["retained_count"]
            < self.MINIMUM_COMPARABLE_PRICES
        ):
            blockers.append(
                (
                    "Au moins trois prix comparables "
                    "sont nécessaires."
                )
            )

        if (
            market_summary["source_domain_count"]
            < self.MINIMUM_SOURCE_DOMAINS
        ):
            blockers.append(
                (
                    "Au moins deux domaines sources "
                    "sont nécessaires."
                )
            )

        try:
            decision_price = (
                self.reference_service.select(
                    summary=market_summary,
                    policy=self.price_policy,
                )
            )
        except ValueError:
            decision_price = None

            blockers.append(
                "Prix de référence indisponible."
            )

        if supplier_offer.shipping_cost is None:
            blockers.append(
                "Coût de livraison manquant."
            )

        if delivery_status == "incomplete":
            blockers.append(
                delivery_result["reason"]
            )

        if delivery_status == "slow":
            warnings.append(
                delivery_result["reason"]
            )

        if (
            supplier_offer.currency
            != market_currency
        ):
            blockers.append(
                (
                    f"Conversion "
                    f"{supplier_offer.currency} "
                    f"vers {market_currency} "
                    "requise."
                )
            )

        status = (
            "incomplete"
            if blockers
            else "ready_for_cost_analysis"
        )

        return self._build_dossier(
            supplier_offer=supplier_offer,
            market_summary=market_summary,
            decision_price=decision_price,
            status=status,
            blockers=blockers,
            warnings=warnings,
            delivery_result=delivery_result,
        )

    def _build_dossier(
        self,
        supplier_offer,
        market_summary,
        decision_price,
        status,
        blockers,
        warnings,
        delivery_result,
    ):
        return {
            "supplier_offer_id": (
                supplier_offer.pk
            ),
            "product_name": (
                supplier_offer.product_name
            ),
            "supplier_name": (
                supplier_offer.supplier.name
            ),
            "supplier_cost": {
                "amount": (
                    supplier_offer.purchase_price
                ),
                "currency": (
                    supplier_offer.currency
                ),
                "shipping_cost": (
                    supplier_offer.shipping_cost
                ),
            },
            "stock": supplier_offer.stock,
            "market": market_summary,
            "decision_price_policy": (
                self.price_policy
            ),
            "decision_price": (
                decision_price
            ),
            "delivery": delivery_result,
            "status": status,
            "blockers": blockers,
            "warnings": warnings,
        }