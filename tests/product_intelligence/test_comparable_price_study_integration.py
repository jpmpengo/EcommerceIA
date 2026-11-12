from decimal import Decimal
from django.test import TestCase
from product_intelligence.models import Supplier, SupplierOffer, ComparablePrice
from product_intelligence.services.comparable_price_persistence import ComparablePricePersistenceService
from product_intelligence.services.comparable_price_study_integration import ComparablePriceStudyIntegrationService


class ComparablePriceStudyIntegrationTests(TestCase):
    def test_direct_candidate_is_integrated_without_losing_existing(self):
        supplier = Supplier.objects.create(name="CJ test", country="CN", website="https://example.com", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, product_name="Test product", purchase_price=Decimal("8.50"), currency="USD")
        def save(url, activate):
            results = [{"product_name": "Comparable test", "observed_price": "24.90", "currency": "EUR", "source_title": "Boutique test", "source_url": url, "evidence": "Produit comparable."}]
            return ComparablePricePersistenceService.save(offer, results, "Test product", "test-model", activate=activate)[0]
        existing = save("https://example.com/old", True)
        candidate = save("https://example.com/new", False)
        for item, segment in ((existing, "different_segment"), (candidate, "direct")):
            item.qualification_status = "retained"
            item.commercial_segment = segment
            item.save(update_fields=["qualification_status", "commercial_segment"])
        result = ComparablePriceStudyIntegrationService.integrate(offer, candidate.collection_batch_id)
        self.assertEqual(result["status"], "integrated")
        self.assertEqual(result["integrated"], 1)
        self.assertEqual(set(ComparablePrice.objects.filter(supplier_offer=offer, is_current=True).values_list("id", flat=True)), {existing.id, candidate.id})

    def test_no_direct_candidate_preserves_active_comparables(self):
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", website="https://cjdropshipping.com", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, product_name="Test product", purchase_price=Decimal("8.50"), currency="USD")
        results = [{"product_name": "Comparable test", "observed_price": "24.90", "currency": "EUR", "source_title": "Boutique test", "source_url": "https://example.com/product", "evidence": "Produit comparable."}]
        active = ComparablePricePersistenceService.save(offer, results, "Test product", "test-model")[0]
        active.qualification_status = "retained"
        active.commercial_segment = "different_segment"
        active.save(update_fields=["qualification_status", "commercial_segment"])
        result = ComparablePriceStudyIntegrationService.integrate(offer, active.collection_batch_id)
        active.refresh_from_db()
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(result["integrated"], 0)
        self.assertTrue(active.is_current)
        self.assertEqual(ComparablePrice.objects.filter(supplier_offer=offer, is_current=True).count(), 1)
