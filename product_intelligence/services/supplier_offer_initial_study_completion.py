from product_intelligence.services.comparable_price_study_completion import ComparablePriceStudyCompletionService
from product_intelligence.services.comparable_price_study_integration import ComparablePriceStudyIntegrationService


class SupplierOfferInitialStudyCompletionService:
    @classmethod
    def analyze(cls, analyzer, offer):
        result = analyzer.process(supplier_offer=offer, create=False)
        if result.get("status") != "incomplete":
            return result
        blockers = result.get("blockers") or []
        comparable_blockers = [b for b in blockers if any(term in b.lower() for term in ("prix comparables", "domaines sources", "prix de référence", "prix de reference"))]
        if not comparable_blockers:
            return result
        batches = offer.comparable_prices.filter(is_current=False, qualification_status="retained", commercial_segment="direct", currency="EUR").exclude(collection_batch_id__isnull=True).order_by("-id").values_list("collection_batch_id", flat=True).distinct()
        for batch_id in list(batches):
            integration = ComparablePriceStudyIntegrationService.integrate(offer, batch_id)
            if integration.get("status") == "integrated":
                result = analyzer.process(supplier_offer=offer, create=False)
                if result.get("status") != "incomplete":
                    return result
        requests = [{"category": "comparable_prices", "research_action": "Rechercher des offres concurrentes directement comparables pour completer les preuves manquantes", "resolution_criterion": "Au moins trois prix comparables retenus, deux domaines sources distincts et un prix de reference exploitable", "reason": b} for b in comparable_blockers]
        completion = ComparablePriceStudyCompletionService.run(offer, requests)
        if completion.get("status") == "integrated":
            return analyzer.process(supplier_offer=offer, create=False)
        return result
