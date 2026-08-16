from decimal import Decimal

from django.test import TestCase

from dashboard.services.emma_briefing_service import (
    EmmaBriefingService,
)
from dashboard.services.priority_advisor import PriorityAdvisor
from product_intelligence.models import ProductOpportunity

from django.contrib.auth import get_user_model

from datetime import timedelta

from django.utils import timezone

from products.models import Category, Product

from dashboard.models import EmmaMemory

from django.core.files.uploadedfile import SimpleUploadedFile




class EmmaBriefingServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="commercant",
            password="mot-de-passe-test",
        )

        self.category = Category.objects.create(
            name="Informatique",
            slug="informatique",
        )

    def test_build_returns_non_empty_greeting(self):
        briefing = EmmaBriefingService.build(self.user)

        greeting = briefing["greeting"]

        self.assertIn(
            "title",
            greeting,
        )

        self.assertIn(
            "message",
            greeting,
        )

        self.assertNotEqual(
            greeting["title"],
            "",
        )

        self.assertNotEqual(
            greeting["message"],
            "",
        )

        self.assertIn(
            "changes",
            briefing,
        )

        self.assertIn(
            "alerts",
            briefing,
        )

        self.assertIn(
            "priorite",
            briefing,
        )

        self.assertIn(
            "next_actions",
            briefing,
        )

        self.assertIn(
            "activity",
            briefing,
        )
    
    def test_build_returns_activity(self):

        briefing = EmmaBriefingService.build(self.user)

        activity = briefing["activity"]

        self.assertIn(
            "products",
            activity,
        )

        self.assertIn(
            "orders",
            activity,
        )

        self.assertIn(
            "opportunities",
            activity,
        )

    def test_build_returns_priority(self):

        briefing = EmmaBriefingService.build(self.user)

        self.assertIn(
            "priorite",
            briefing,
        )

    def test_priority_is_none_when_no_action_exists(self):

        briefing = EmmaBriefingService.build(self.user)

        self.assertIsNone(
            briefing["priorite"],
        )

    def test_priority_is_first_approved_opportunity(self):

        opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth AAC",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Casque Bluetooth de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=self.category,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        priority = PriorityAdvisor.get_priority()

        self.assertEqual(
            priority["title"],
            "Publier Casque Bluetooth AAC",
        )

    def test_first_visit_returns_welcome_greeting(self):
        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertEqual(
            briefing["greeting"]["title"],
            "Bonjour",
        )

        self.assertIsNone(
            briefing["greeting"]["previous_visit"],
        )

    def test_next_visit_returns_welcome_back_greeting(self):
        EmmaBriefingService.build(self.user)

        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertEqual(
            briefing["greeting"]["title"],
            "Bon retour",
        )

        self.assertIsNotNone(
            briefing["greeting"]["previous_visit"],
        )  

    def test_build_includes_new_opportunity_in_changes(self):
        EmmaBriefingService.build(self.user)

        previous_visit = timezone.now()

        memory = self.user.emma_memory
        memory.last_visit = previous_visit
        memory.save(
            update_fields=[
                "last_visit",
                "updated_at",
            ]
        )

        ProductOpportunity.objects.create(
            name="Nouvelle opportunité",
            source_name="Fournisseur test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="detected",
            description="Opportunité récente avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            initial_stock=5,
            category=self.category,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertIn(
            "1 nouvelle opportunité",
            briefing["changes"][0]["message"],
        )

    def test_build_returns_progress(self):

        # Première visite : Emma mémorise la date.
        EmmaBriefingService.build(self.user)

        # Un produit est publié après cette visite.
        Product.objects.create(
            category=self.category,
            name="Casque Bluetooth AAC",
            description="Produit de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            price=Decimal("79.90"),
            stock=5,
            is_available=True,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        # Deuxième visite : Emma construit un nouveau briefing.
        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertIn(
            "progress",
            briefing,
        )

        self.assertEqual(
            len(briefing["progress"]),
            1,
        )

        self.assertEqual(
            briefing["progress"][0]["icon"],
            "🎉",
        )

        self.assertIn(
            "publié",
            briefing["progress"][0]["message"],
        )
    
    def test_build_returns_progress(self):
     
        EmmaBriefingService.build(self.user)

        Product.objects.create(
            category=self.category,
            name="Casque Bluetooth AAC",
            description="Produit de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            price=Decimal("79.90"),
            stock=5,
            is_available=True,
            image=SimpleUploadedFile(
                "casque.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
        )

        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertIn(
            "progress",
            briefing,
        )

        self.assertEqual(
            len(briefing["progress"]),
            1,
        )

        self.assertEqual(
            briefing["progress"][0]["icon"],
            "🎉",
        )

        self.assertIn(
            "publié",
            briefing["progress"][0]["message"],
        )

    def test_first_visit_of_day_returns_bonjour(self):
        yesterday = (
            timezone.now() - timedelta(days=1)
        )

        EmmaMemory.objects.update_or_create(
            user=self.user,
            defaults={
                "last_visit": yesterday,
            },
        )

        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertEqual(
            briefing["greeting"]["title"],
            "Bonjour",
        )

    def test_second_visit_of_day_returns_bon_retour(self):
        now = timezone.localtime()

        earlier_today = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        EmmaMemory.objects.update_or_create(
            user=self.user,
            defaults={
                "last_visit": earlier_today,
            },
        )

        briefing = EmmaBriefingService.build(
            self.user
        )

        self.assertEqual(
            briefing["greeting"]["title"],
            "Bon retour",
        ) 


