from decimal import Decimal

from django.test import TestCase

from dashboard.services.business_advisor import BusinessAdvisor
from orders.models import Order
from products.models import Category, Product
from product_intelligence.models import ProductOpportunity

from datetime import timedelta
from django.utils import timezone

class BusinessAdvisorTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Informatique",
        )

        Product.objects.create(
            category=self.category,
            name="Produit actif",
            description="Produit disponible avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            price=Decimal("49.90"),
            stock=10,
            is_available=True,
        )

        self.opportunity = ProductOpportunity.objects.create(
            name="Clavier mécanique",
            source_name="Fournisseur test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("60.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=90,
            competition_score=40,
            status="approved",
            description="Clavier mécanique de test avec une description suffisamment détaillée "
                        "pour permettre sa publication dans la boutique.",
            category=self.category,
            initial_stock=5,
        )

    '''
    Règle métier :
            Le Dashboard reçoit toujours les statistiques principales.
            Le Dashboard reçoit toujours les statistiques dont il a besoin :
                product_count
                active_product_count
                order_count
                opportunity_count
    '''
    def test_business_brief_contains_statistics(self):
        advisor = BusinessAdvisor()

        brief = advisor.get_business_brief()

        self.assertIn(
            "statistics",
            brief,
        )

        statistics = brief["statistics"]

        self.assertEqual(
            statistics["product_count"],
            1,
        )

        self.assertEqual(
            statistics["active_product_count"],
            1,
        )

        self.assertEqual(
            statistics["opportunity_count"],
            1,
        )

        self.assertIn(
            "order_count",
            statistics,
        )

    '''
    Règle métier :
            Le Dashboard doit toujours recevoir les opportunités prioritaires.
            Le Dashboard doit afficher les opportunités lorsqu'elles existent. Sinon, il doit afficher une liste vide.
    '''
    def test_business_brief_contains_top_opportunities(self):
        advisor = BusinessAdvisor()

        brief = advisor.get_business_brief()

        self.assertIn(
            "top_opportunities",
            brief,
        )

        self.assertIsInstance(
            brief["top_opportunities"],
            list,
        )

        self.assertEqual(
            len(brief["top_opportunities"]),
            1,
        )
    
    def test_business_brief_allows_no_top_opportunities(self):
        ProductOpportunity.objects.all().delete()

        advisor = BusinessAdvisor()
        brief = advisor.get_business_brief()

        self.assertEqual(
            brief["top_opportunities"],
            [],
        )

    '''
    Règle métier :
            Le Dashboard ne doit jamais afficher plus de trois opportunités prioritaires.
    '''
    def test_business_brief_limits_top_opportunities_to_three(self):

        for i in range(3):
            ProductOpportunity.objects.create(
                name=f"Produit {i}",
                source_name="Test",
                supplier_price=Decimal("20.00"),
                market_price=Decimal("60.00"),
                shipping_cost=Decimal("5.00"),
                other_costs=Decimal("5.00"),
                demand_score=90,
                competition_score=40,
                status="approved",
                description="Produit de test avec une description suffisamment détaillée "
                            "pour permettre sa publication dans la boutique.",
                category=self.category,
                initial_stock=5,
            )

        advisor = BusinessAdvisor()

        brief = advisor.get_business_brief()

        self.assertEqual(
            len(brief["top_opportunities"]),
            3,
        )

    '''
    Règle métier :
            Une opportunité reportée ne doit pas apparaître dans les recommandations tant que la date de report n'est pas atteinte.
    '''
    def test_business_brief_hides_postponed_opportunities(self):
        self.opportunity.postponed_until = (
            timezone.now() + timedelta(days=14)
        )
        self.opportunity.save()

        advisor = BusinessAdvisor()

        brief = advisor.get_business_brief()

        self.assertEqual(
            len(brief["top_opportunities"]),
            0,
        )

     
    '''
    Règle métier :
            Une opportunité dont la date de report est dépassée redevient automatiquement visible.
    '''
    def test_business_brief_visibles_postponed_opportunities(self):
        self.opportunity.postponed_until = (
            timezone.now() - timedelta(days=14)
        )
        self.opportunity.save()

        advisor = BusinessAdvisor()

        brief = advisor.get_business_brief()

        self.assertEqual(
            len(brief["top_opportunities"]),
            1,
        )
