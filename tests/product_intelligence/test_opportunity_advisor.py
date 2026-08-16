from decimal import Decimal

from django.test import TestCase

from product_intelligence.models import ProductOpportunity
from product_intelligence.services.advisor import OpportunityAdvisor


class OpportunityAdvisorTests(TestCase):
    def setUp(self):
        self.opportunity = ProductOpportunity.objects.create(
            name="Casque Bluetooth",
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
        )
    
    '''
    Règle métier :
            Tant qu’aucune stratégie utilisateur n’est appliquée, la priorité correspond au score de l’opportunité.
            La priorité d'une opportunité est égale à son score d'opportunité.

            Aujourd'hui :
                    Priorité = Score

            Demain, nous pourrions avoir :
                    Priorité =  Score d'opportunité
                                + bonus saisonnier
                                + bonus stratégie commerçant
                                - pénalité concurrence
    '''
    def test_calculate_priority_uses_opportunity_score(self):
        priority = OpportunityAdvisor.calculate_priority(
            self.opportunity
        )

        self.assertEqual(
            priority,
            self.opportunity.opportunity_score,
        )

    '''
     Règle métier :
            Une opportunité doit toujours produire une recommandation compréhensible.
            Le commerçant reçoit toujours une recommandation lisible.
            Une opportunité analysée produit toujours une recommandation structurée, avec une décision, des raisons et un score.
    '''
    def test_get_recommendation_returns_complete_recommendation(self):
        recommendation = OpportunityAdvisor.get_recommendation(
            self.opportunity
        )

        self.assertIsInstance(
            recommendation,
            dict,
        )

        self.assertIn(
            "decision",
            recommendation,
        )

        self.assertIn(
            "reasons",
            recommendation,
        )

        self.assertIn(
            "score",
            recommendation,
        )

        self.assertNotEqual(
            recommendation["decision"],
            "",
        )

        self.assertGreater(
            len(recommendation["reasons"]),
         0,
        )

    '''
      Règle métier :
            Les opportunités sont classées par priorité décroissante.
            Je vérifie simplement la règle : Le premier a un score supérieur ou égal au dernier.
        
    '''
    def test_rank_opportunities_orders_by_priority(self):
        low = ProductOpportunity.objects.create(
            name="Produit faible",
            source_name="Test",
            supplier_price=Decimal("20.00"),
            market_price=Decimal("30.00"),
            shipping_cost=Decimal("5.00"),
            other_costs=Decimal("5.00"),
            demand_score=20,
            competition_score=90,
            status="approved",
            description="Faible opportunité",
            initial_stock=5,
        )

        ranked = OpportunityAdvisor.rank_opportunities(
            ProductOpportunity.objects.all()
        )

        self.assertGreaterEqual(
            ranked[0].opportunity_score,
            ranked[-1].opportunity_score,
        )