from product_intelligence.services.comparable_price_runner_factory import ComparablePriceRunnerFactory
from product_intelligence.services.comparable_price_study_integration import ComparablePriceStudyIntegrationService


class ComparablePriceStudyCompletionService:
    @classmethod
    def run(cls, supplier_offer, study_blockers):
        runner = ComparablePriceRunnerFactory.build()
        collection_service = runner.research_pipeline.comparable_price_collection
        comparables = collection_service.collect(supplier_offer, study_blockers=study_blockers, activate=False)
        if not comparables:
            return {"status": "no_results", "retained": 0}
        batch_id = comparables[0].collection_batch_id
        qualification = runner.qualification_service.qualify(supplier_offer, collection_batch_id=batch_id)
        if qualification["retained"] == 0:
            return {"status": "no_retained", "batch_id": str(batch_id), "retained": 0, "rejected": qualification["rejected"]}
        retained = list(supplier_offer.comparable_prices.filter(collection_batch_id=batch_id, qualification_status="retained"))
        classification = runner.commercial_classification_service.classify_and_save(supplier_offer, retained, collection_batch_id=batch_id)
        integration = ComparablePriceStudyIntegrationService.integrate(supplier_offer, batch_id)
        return {"status": integration["status"], "batch_id": str(batch_id), "retained": qualification["retained"], "rejected": qualification["rejected"], "classified": classification["saved_count"], "integrated": integration["integrated"]}
