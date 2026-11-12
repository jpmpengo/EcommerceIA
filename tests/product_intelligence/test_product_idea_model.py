from django.test import TestCase

from product_intelligence.models import ProductIdea


class ProductIdeaModelTests(TestCase):

    def test_demand_signal_assessments_defaults_to_empty_list(self):
        idea = ProductIdea.objects.create(
            name="Produit test",
            customer_problem="Problème test",
            target_customer="Client test",
            reason_to_study="Raison test",
            countries=["FR"],
        )

        self.assertEqual(
            idea.demand_signal_assessments,
            [],
        )

    def test_idea_score_defaults_to_zero(self):
        idea = ProductIdea.objects.create(
            name="Produit score test",
            customer_problem="Probleme test",
            target_customer="Client test",
            reason_to_study="Raison test",
            countries=["FR"],
        )

        self.assertEqual(
            idea.idea_score,
            0,
        )

    def test_selection_source_defaults_to_empty_string(self):
        idea = ProductIdea.objects.create(
            name="Produit selection test",
            customer_problem="Probleme test",
            target_customer="Client test",
            reason_to_study="Raison test",
            countries=["FR"],
        )

        self.assertEqual(
            idea.selection_source,
            "",
        )
