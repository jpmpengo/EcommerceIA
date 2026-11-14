from decimal import Decimal

from product_intelligence.services.comparable_price_runner_factory import ComparablePriceRunnerFactory
from product_intelligence.services.comparable_price_logistics_search import ComparablePriceLogisticsSearchService


class ComparablePriceLogisticsCompletionService:
    @classmethod
    def run(cls, supplier_offer, destination_country="FR"):
        comparables = list(supplier_offer.comparable_prices.filter(is_current=True, qualification_status="retained"))
        if not comparables:
            return {"status": "no_comparables", "updated": 0}
        runner = ComparablePriceRunnerFactory.build(destination_country=destination_country)
        client = runner.research_pipeline.comparable_price_collection.search_service.client
        response = ComparablePriceLogisticsSearchService(client).search(comparables, destination_country)
        by_id = {c.id: c for c in comparables}
        updated = 0
        evidence_found = False
        for result in response["results"]:
            comparable = by_id.get(result["comparable_id"])
            if comparable is None or not result.get("shipping_evidence") or result.get("shipping_destination_country") != destination_country:
                continue
            evidence_found = True
            fields = []
            for name in ("shipping_days_min", "shipping_days_max", "shipping_currency", "free_shipping", "shipping_destination_country", "shipping_evidence"):
                value = result.get(name)
                if value is not None and getattr(comparable, name) != value:
                    setattr(comparable, name, value)
                    fields.append(name)
            if result.get("shipping_cost") is not None:
                value = Decimal(str(result.get("shipping_cost")))
                if comparable.shipping_cost != value:
                    comparable.shipping_cost = value
                    fields.append("shipping_cost")
            if fields:
                comparable.save(update_fields=fields)
                updated += 1
        return {"status": "updated" if evidence_found else "unresolved", "updated": updated, "total": len(comparables), "verification_performed": True}
