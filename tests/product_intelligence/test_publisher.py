from decimal import Decimal

from products.models import Category
from product_intelligence.models import ProductOpportunity
from product_intelligence.services.publisher import OpportunityPublisher

from products.models import Product

from django.core.files.uploadedfile import SimpleUploadedFile

import os
import tempfile

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import (
    TestCase,
    override_settings,
)

class OpportunityPublisherTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Audio",
        )

        self.opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth",
            source_name="Test",
            supplier_price=Decimal("20"),
            market_price=Decimal("60"),
            shipping_cost=Decimal("5"),
            other_costs=Decimal("5"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Très bon casque",
            category=self.category,
            initial_stock=10,
        )

        self.opportunity.image = SimpleUploadedFile(
            "test.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        self.opportunity.save(
            update_fields=["image"]
        )

    def test_publish_valid_opportunity(self):
        product = OpportunityPublisher.publish(
            self.opportunity
        )

        self.assertIsNotNone(product.pk)

        self.opportunity.refresh_from_db()

        self.assertEqual(
            self.opportunity.status,
            "published",
        )

        self.assertEqual(
            self.opportunity.published_product,
            product,
        )

    def test_publish_requires_category(self):
        self.opportunity.category = None

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(
                self.opportunity
            )

        self.assertIn(
            "catégorie",
            str(context.exception),
        )


    def test_publish_requires_approved_status(self):
        self.opportunity.status = "detected"

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(self.opportunity)

        self.assertIn(
            "approuvée",
            str(context.exception),
        )
        
    def test_publish_requires_description(self):
        self.opportunity.description = ""

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(self.opportunity)

        self.assertIn(
            "description",
            str(context.exception),
        )

    def test_publish_requires_stock(self):
        self.opportunity.initial_stock = 0

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(self.opportunity)

        self.assertIn(
            "stock initial",
            str(context.exception),
        )

    def test_publish_already_published(self):
        product = Product.objects.create(
            category=self.category,
            name="Produit déjà publié",
            description="Produit de test",
            price=50,
            stock=5,
            is_available=True,
        )

        self.opportunity.published_product = product
        self.opportunity.status = "published"
        self.opportunity.save()

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(
                self.opportunity
            )

        self.assertIn(
            "déjà publiée",
            str(context.exception),
        )

    def test_publish_requires_image(self):
        self.opportunity.image = None

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(
                self.opportunity
            )

        self.assertIn(
            "image",
            str(context.exception),
        )   

    def test_publish_requires_positive_recommended_price(self):
        self.opportunity.recommended_price = Decimal("0.00")

        with self.assertRaises(ValueError) as context:
            OpportunityPublisher.publish(
                self.opportunity
            )

        self.assertIn(
            "prix conseill",
            str(context.exception),
        )

    def test_publish_moves_image_to_product_and_removes_opportunity_image(
        self,
    ):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(
                MEDIA_ROOT=media_root,
            ):
                category = Category.objects.create(
                    name="Électronique",
                    slug="electronique",
                )

                image = SimpleUploadedFile(
                    "temporary.jpg",
                    b"fake-image-content",
                    content_type="image/jpeg",
                )

                opportunity = ProductOpportunity.objects.create(
                    name="Wireless Charger",
                    source_name="CJdropshipping",
                    supplier_price=Decimal("4.53"),
                    market_price=Decimal("27.90"),
                    shipping_cost=Decimal("0.00"),
                    other_costs=Decimal("0.00"),
                    description="Produit test",
                    category=category,
                    image=image,
                    initial_stock=10,
                    status="approved",
                )

                old_image_name = opportunity.image.name
                old_image_path = opportunity.image.path

                self.assertTrue(
                    os.path.exists(
                        old_image_path
                    )
                )

                product = OpportunityPublisher.publish(
                    opportunity
                )

                opportunity.refresh_from_db()
                product.refresh_from_db()

                self.assertTrue(
                    bool(product.image)
                )

                self.assertFalse(
                    bool(opportunity.image)
                )

                self.assertNotEqual(
                    product.image.name,
                    old_image_name,
                )

                self.assertTrue(
                    os.path.exists(
                        product.image.path
                    )
                )

                self.assertFalse(
                    os.path.exists(
                        old_image_path
                    )
                )
