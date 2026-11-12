from unittest.mock import Mock, patch

from django.test import TestCase

from product_intelligence.models import ProductIdea, ProductIdeaVisualReference
from product_intelligence.services.product_idea_visual_reference_collection import ProductIdeaVisualReferenceCollectionService


class ProductIdeaVisualReferenceCollectionServiceTests(TestCase):

    def test_preserves_existing_references_when_new_images_are_inaccessible(self):
        idea = ProductIdea.objects.create(name="Neck fan", customer_problem="Heat", target_customer="Travelers", reason_to_study="Demand", countries=["FR"])
        old = ProductIdeaVisualReference.objects.create(product_idea=idea, supplier_search_keyword="neck fan", product_name="Old fan", image_url="https://example.com/old.jpg")
        search_service = Mock()
        search_service.search.return_value = {"visual_references": [{"supplier_search_keyword": "neck fan", "product_name": "New fan", "image_url": "https://example.com/broken.jpg"}]}
        service = ProductIdeaVisualReferenceCollectionService(search_service=search_service)
        with patch("product_intelligence.services.product_idea_visual_reference_collection.VisualImageAccessibilityService.is_accessible", return_value=False):
            result = service.collect(product_idea=idea)
        self.assertEqual(result, [])
        self.assertEqual(list(idea.visual_references.values_list("id", flat=True)), [old.id])

    def test_replaces_existing_visual_references(self):
        idea = ProductIdea.objects.create(name="Cycling", customer_problem="Visibility", target_customer="Cyclists", reason_to_study="Demand", countries=["FR"], supplier_search_keywords=["USB rechargeable bike light"])
        ProductIdeaVisualReference.objects.create(product_idea=idea, supplier_search_keyword="USB rechargeable bike light", product_name="Old light", image_url="https://example.com/old.jpg")
        search_service = Mock()
        search_service.search.return_value = {"visual_references": [{"supplier_search_keyword": "USB rechargeable bike light", "product_name": "New light", "source_title": "Source", "source_url": "https://example.com/product", "image_url": "https://example.com/new.jpg"}]}
        service = ProductIdeaVisualReferenceCollectionService(search_service=search_service, model_name="test-model")
        with patch("product_intelligence.services.product_idea_visual_reference_collection.VisualImageAccessibilityService.is_accessible", return_value=True):
            service.collect(product_idea=idea)
        refs = list(idea.visual_references.order_by("id"))
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].product_name, "New light")
        self.assertEqual(refs[0].image_url, "https://example.com/new.jpg")
        self.assertEqual(refs[0].model_name, "test-model")
