from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
    ProductIdeaVisualReference,
)


class ProductIdeaVisualReferenceTests(TestCase):

    def test_links_image_to_idea_supplier_keyword(self):
        idea = ProductIdea.objects.create(
            name="Cycling accessories",
            customer_problem="Visibility",
            target_customer="Cyclists",
            reason_to_study="Demand",
            countries=["FR"],
            supplier_search_keywords=[
                "USB rechargeable bike light",
            ],
        )

        reference = ProductIdeaVisualReference.objects.create(
            product_idea=idea,
            supplier_search_keyword="USB rechargeable bike light",
            product_name="Rechargeable bike light",
            image_url="https://example.com/bike-light.jpg",
        )

        self.assertEqual(reference.product_idea, idea)
        self.assertEqual(
            reference.supplier_search_keyword,
            "USB rechargeable bike light",
        )
        self.assertEqual(
            reference.image_url,
            "https://example.com/bike-light.jpg",
        )
