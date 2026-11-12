from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
    ProductIdeaVisualReference,
    Supplier,
    SupplierOffer,
)
from product_intelligence.services.supplier_offer_visual_matching import (
    SupplierOfferVisualMatchingService,
)


class SupplierOfferVisualMatchingServiceTests(TestCase):

    def test_renews_inaccessible_reference_before_matching(self):
        idea = ProductIdea.objects.create(name="Neck fan", customer_problem="Heat", target_customer="Travelers", reason_to_study="Demand", countries=["FR"])
        ProductIdeaVisualReference.objects.create(product_idea=idea, supplier_search_keyword="neck fan", product_name="Old fan", image_url="https://example.com/broken.jpg")
        supplier = Supplier.objects.create(name="CJ renewal", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, product_idea=idea, product_name="Fan", purchase_price=Decimal("8.50"), currency="USD", image_url="https://example.com/fan.jpg", supplier_search_keyword="neck fan")
        def renew(product_idea):
            ProductIdeaVisualReference.objects.filter(product_idea=product_idea).delete()
            ProductIdeaVisualReference.objects.create(product_idea=product_idea, supplier_search_keyword="neck fan", product_name="New fan", image_url="https://example.com/valid.jpg")
        collector = Mock(side_effect=renew)
        matching_service = Mock()
        matching_service.match.return_value = {"matches": []}
        service = SupplierOfferVisualMatchingService(matching_service=matching_service, reference_collector=collector)
        with patch("product_intelligence.services.supplier_offer_visual_matching.VisualImageAccessibilityService.is_accessible", side_effect=lambda url: url.endswith("valid.jpg")):
            service.match([offer])
        collector.assert_called_once_with(idea)
        matching_service.match.assert_called_once_with(references=[{"product_name": "New fan", "image_url": "https://example.com/valid.jpg"}], supplier_offers=[offer], product_idea_name=idea.name)

    def test_skips_inaccessible_reference_without_validating_offer(self):
        idea = ProductIdea.objects.create(name="Neck fan", customer_problem="Heat", target_customer="Travelers", reason_to_study="Demand", countries=["FR"])
        ProductIdeaVisualReference.objects.create(product_idea=idea, supplier_search_keyword="neck fan", product_name="Fan", image_url="https://example.com/broken.jpg")
        supplier = Supplier.objects.create(name="CJ test", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, product_idea=idea, product_name="Fan", purchase_price=Decimal("8.50"), currency="USD", image_url="https://example.com/fan.jpg", supplier_search_keyword="neck fan")
        matching_service = Mock()
        service = SupplierOfferVisualMatchingService(matching_service=matching_service)
        with patch("product_intelligence.services.supplier_offer_visual_matching.VisualImageAccessibilityService.is_accessible", return_value=False):
            result = service.match([offer])
        matching_service.match.assert_not_called()
        self.assertEqual(result["matches"], [])
        offer.refresh_from_db()
        self.assertFalse(offer.visual_match_classification)

    def test_uses_only_images_associated_with_offer_keyword(self):
        idea = ProductIdea.objects.create(name="Cycling", customer_problem="Visibility", target_customer="Cyclists", reason_to_study="Demand", countries=["FR"], supplier_search_keywords=["USB rechargeable bike light", "reflective cycling vest"])
        ProductIdeaVisualReference.objects.create(product_idea=idea, supplier_search_keyword="USB rechargeable bike light", product_name="Bike light", image_url="https://example.com/light.jpg")
        ProductIdeaVisualReference.objects.create(product_idea=idea, supplier_search_keyword="reflective cycling vest", product_name="Vest", image_url="https://example.com/vest.jpg")
        supplier = Supplier.objects.create(name="CJdropshipping", country="CN", supplier_type="dropshipper")
        offer = SupplierOffer.objects.create(supplier=supplier, product_idea=idea, product_name="Bike Light", purchase_price=Decimal("8.50"), currency="USD", image_url="https://example.com/cj-light.jpg", supplier_search_keyword="USB rechargeable bike light")
        matching_service = Mock()
        matching_service.match.return_value = {"matches": [{"offer_id": offer.id, "classification": "rejected", "visual_score": 28, "same_product_probability": 5, "evidence": "Phare avant seul.", "differences": ["Absence de feu arriere"]}]}
        service = SupplierOfferVisualMatchingService(matching_service=matching_service)
        with patch("product_intelligence.services.supplier_offer_visual_matching.VisualImageAccessibilityService.is_accessible", return_value=True):
            service.match([offer])
        matching_service.match.assert_called_once_with(references=[{"product_name": "Bike light", "image_url": "https://example.com/light.jpg"}], supplier_offers=[offer], product_idea_name=idea.name)
        offer.refresh_from_db()
        self.assertEqual(offer.visual_match_classification, "rejected")
        self.assertEqual(offer.visual_score, 28)
        self.assertEqual(offer.same_product_probability, 5)
        self.assertEqual(offer.visual_match_evidence, "Phare avant seul.")
        self.assertEqual(offer.visual_match_differences, ["Absence de feu arriere"])
