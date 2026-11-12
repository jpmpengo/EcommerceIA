from decimal import Decimal
from orders.services.customs_duty_service import CustomsDutyService


class SupplierOfferAnalysisPipeline:

    CURRENCY_BLOCKER_PREFIX = "Conversion "

    def __init__(
        self,
        evaluation_service,
        base_cost_service,
        cost_calculation_service,
        opportunity_service,
        customs_duty_service=None,
        minimum_profitable_price_service=None,
        minimum_projected_profit=Decimal("0.01"),
        minimum_margin_rate=Decimal("10.00"),
    ):
        self.evaluation_service = evaluation_service
        self.base_cost_service = base_cost_service
        self.cost_calculation_service = (
            cost_calculation_service
        )
        self.opportunity_service = opportunity_service
        self.customs_duty_service = customs_duty_service
        self.minimum_profitable_price_service = minimum_profitable_price_service
        self.minimum_projected_profit = minimum_projected_profit
        self.minimum_margin_rate = minimum_margin_rate

    def process(
        self,
        supplier_offer,
        market_currency="EUR",
        create=False,
    ):
        dossier = self.evaluation_service.prepare(
            supplier_offer=supplier_offer,
            market_currency=market_currency,
        )

        blockers = [
            blocker
            for blocker in dossier["blockers"]
            if not blocker.startswith(
                self.CURRENCY_BLOCKER_PREFIX
            )
        ]

        dossier["blockers"] = blockers
        if not blockers:
            dossier["status"] = "ready_for_cost_analysis"

        if blockers:
            return {
                "status": "incomplete",
                "blockers": blockers,
                "warnings": dossier["warnings"],
                "dossier": dossier,
                "base_cost": None,
                "cost_analysis": None,
                "opportunity": None,
            }

        base_cost = self.base_cost_service.calculate(
            supplier_offer=supplier_offer,
            target_currency=market_currency,
        )

        import_duty = None
        customs = None
        if getattr(supplier_offer, "customs_included", None) is True:
            import_duty = Decimal("0.00")
        elif self.customs_duty_service is not None:
            if (supplier_offer.stock_country or supplier_offer.supplier.country or "").upper() not in CustomsDutyService.EU_COUNTRIES and (supplier_offer.shipping_country or "").upper() in CustomsDutyService.EU_COUNTRIES and base_cost["purchase_converted"] > CustomsDutyService.LOW_VALUE_LIMIT:
                return {"status": "customs_excluded", "blockers": ["Valeur douaniere superieure a 150 EUR."], "warnings": dossier["warnings"], "dossier": dossier, "base_cost": base_cost, "cost_analysis": None, "customs": None, "opportunity": None}
            customs = self.customs_duty_service.estimate(
                origin_country=(supplier_offer.stock_country or supplier_offer.supplier.country),
                destination_country=supplier_offer.shipping_country,
                intrinsic_value=base_cost["purchase_converted"],
                quantity=1,
            )
            import_duty = customs["amount"]

        calculation_arguments = {
            "decision_price": dossier["decision_price"],
            "base_cost": base_cost["base_cost"],
            "currency": market_currency,
        }
        if import_duty is not None:
            calculation_arguments["import_duty"] = import_duty
        cost_analysis = self.cost_calculation_service.calculate(
            **calculation_arguments
        )

        if self.minimum_profitable_price_service is not None:
            profitable_result = self.minimum_profitable_price_service.calculate(
                base_cost=base_cost["base_cost"],
                currency=market_currency,
                import_duty=import_duty,
                minimum_margin_rate=self.minimum_margin_rate,
                minimum_profit=self.minimum_projected_profit,
            )
            minimum_price = profitable_result["decision_price"]
            dossier["minimum_profitable_price"] = minimum_price
            if dossier["decision_price"] < minimum_price:
                dossier["decision_price"] = minimum_price
                dossier["decision_price_policy"] = "minimum_profitable"
                cost_analysis = profitable_result["cost_analysis"]
        if cost_analysis["projected_profit"] <= 0:
            return {
                "status": "unprofitable",
                "blockers": ["Vente à perte ou benefice net non positif."],
                "warnings": dossier["warnings"],
                "dossier": dossier,
                "base_cost": base_cost,
                "cost_analysis": cost_analysis,
                "customs": customs,
                "opportunity": None,
            }

        dossier["status"] = "ready_for_opportunity"

        opportunity = None

        if create:
            opportunity = (
                self.opportunity_service
                .create_analyzed_opportunity(
                    offer=supplier_offer,
                    decision_price=(
                        dossier["decision_price"]
                    ),
                    base_cost_result=base_cost,
                    cost_result=cost_analysis,
                    market_collection_batch_id=(
                        dossier.get("market", {}).get(
                            "collection_batch_id"
                        )
                    ),
                    market_summary=dossier.get("market", {}),
                )
            )

        return {
            "status": (
                "created"
                if opportunity is not None
                else "ready_for_opportunity"
            ),
            "blockers": [],
            "warnings": dossier["warnings"],
            "dossier": dossier,
            "base_cost": base_cost,
            "cost_analysis": cost_analysis,
            "customs": customs,
            "opportunity": opportunity,
        }
