from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.models import ProductIdea
from product_intelligence.services.product_idea_nightly_orchestrator import (
    ProductIdeaNightlyOrchestratorService,
)


class ProductIdeaNightlyOrchestratorServiceTests(TestCase):

    def test_processes_proposed_ideas_by_score_descending_with_stable_tie_break(self):
        low = ProductIdea.objects.create(
            name="Low",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=30,
        )
        high_oldest = ProductIdea.objects.create(
            name="High oldest",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=75,
        )
        high_newest = ProductIdea.objects.create(
            name="High newest",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=75,
        )

        selection_service = Mock()
        selection_service.select.side_effect = lambda idea, **kwargs: idea
        analysis_service = Mock()

        ProductIdeaNightlyOrchestratorService.run(
            selection_service=selection_service,
            analysis_service=analysis_service,
        )

        selected_ids = [
            call.args[0].pk
            for call in selection_service.select.call_args_list
        ]

        self.assertTrue(
            all(
                call.kwargs["selection_source"] == "automatic"
                for call in selection_service.select.call_args_list
            )
        )

        self.assertEqual(
            selected_ids,
            [high_oldest.pk, high_newest.pk, low.pk],
        )


        analyzed_ids = [
            call.kwargs["product_idea"].pk
            for call in analysis_service.run.call_args_list
        ]

        self.assertEqual(
            analyzed_ids,
            [high_oldest.pk, high_newest.pk, low.pk],
        )


        returned_idea = Mock(pk=9999)
        selection_service.reset_mock()
        analysis_service.reset_mock()
        selection_service.select.return_value = returned_idea
        selection_service.select.side_effect = None

        ProductIdeaNightlyOrchestratorService.run(
            selection_service=selection_service,
            analysis_service=analysis_service,
        )

        self.assertIs(
            analysis_service.run.call_args_list[0].kwargs["product_idea"],
            returned_idea,
        )

    def test_continues_with_next_idea_when_analysis_fails(self):
        first = ProductIdea.objects.create(
            name="First",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=90,
        )
        second = ProductIdea.objects.create(
            name="Second",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=80,
        )

        selection_service = Mock()
        selection_service.select.side_effect = lambda idea, **kwargs: idea

        analysis_service = Mock()
        analysis_service.run.side_effect = [
            RuntimeError("Erreur technique"),
            {"product_idea_id": second.pk},
        ]

        result = ProductIdeaNightlyOrchestratorService.run(
            selection_service=selection_service,
            analysis_service=analysis_service,
        )

        analyzed_ids = [
            call.kwargs["product_idea"].pk
            for call in analysis_service.run.call_args_list
        ]

        self.assertEqual(
            analyzed_ids,
            [first.pk, second.pk],
        )

        self.assertEqual(
            result["succeeded_ids"],
            [second.pk],
        )
        self.assertEqual(
            result["failed_ids"],
            [first.pk],
        )

        self.assertEqual(
            result["failures"],
            [
                {
                    "product_idea_id": first.pk,
                    "stage": "analysis",
                    "error": "Erreur technique",
                }
            ],
        )

    def test_continues_with_next_idea_when_selection_fails(self):
        first = ProductIdea.objects.create(
            name="Selection failure",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=90,
        )
        second = ProductIdea.objects.create(
            name="Selection success",
            customer_problem="Probleme",
            target_customer="Client",
            reason_to_study="Raison",
            countries=["FR"],
            idea_score=80,
        )

        selection_service = Mock()
        selection_service.select.side_effect = [
            ValueError("Erreur de selection"),
            second,
        ]
        analysis_service = Mock()

        result = ProductIdeaNightlyOrchestratorService.run(
            selection_service=selection_service,
            analysis_service=analysis_service,
        )

        self.assertEqual(
            [call.kwargs["product_idea"].pk for call in analysis_service.run.call_args_list],
            [second.pk],
        )
        self.assertEqual(result["succeeded_ids"], [second.pk])
        self.assertEqual(result["failed_ids"], [first.pk])
        self.assertEqual(
            result["failures"],
            [
                {
                    "product_idea_id": first.pk,
                    "stage": "selection",
                    "error": "Erreur de selection",
                }
            ],
        )

    def test_can_process_only_one_requested_proposed_idea(self):
        first = ProductIdea.objects.create(name="First", customer_problem="Probleme", target_customer="Client", reason_to_study="Raison", countries=["FR"], idea_score=90)
        second = ProductIdea.objects.create(name="Second", customer_problem="Probleme", target_customer="Client", reason_to_study="Raison", countries=["FR"], idea_score=80)

        selection_service = Mock()
        selection_service.select.side_effect = lambda idea, **kwargs: idea
        analysis_service = Mock()

        result = ProductIdeaNightlyOrchestratorService.run(
            idea_id=second.pk,
            selection_service=selection_service,
            analysis_service=analysis_service,
        )

        self.assertEqual([call.args[0].pk for call in selection_service.select.call_args_list], [second.pk])
        self.assertEqual([call.kwargs["product_idea"].pk for call in analysis_service.run.call_args_list], [second.pk])
        self.assertEqual(result["succeeded_ids"], [second.pk])

    def test_generates_ideas_when_none_are_proposed(self):
        from unittest.mock import patch

        with patch("product_intelligence.services.product_idea_generation.ProductIdeaGenerationService.generate") as generate:
            ProductIdeaNightlyOrchestratorService.run()

        generate.assert_called_once_with()

    def test_study_comparables_trigger_completion_and_one_reevaluation(self):
        from unittest.mock import patch
        from product_intelligence.models import ProductOpportunity
        idea = ProductIdea.objects.create(name="Study test", customer_problem="Probleme", target_customer="Client", reason_to_study="Raison", countries=["FR"], idea_score=80)
        selection = Mock()
        selection.select.side_effect = lambda item, **kwargs: item
        analysis = Mock()
        analysis.run.return_value = {"processed_opportunity_ids": [123]}
        opportunity = Mock(spec=ProductOpportunity)
        opportunity.supplier_offer_id = 456
        opportunity.supplier_offer = Mock()
        recommendation = Mock(decision="study", study_blockers=[{"category": "comparable_prices", "blocker": "Comparables directs absents"}], completion_history=[])
        with patch("product_intelligence.services.product_idea_nightly_orchestrator.ProductOpportunity.objects.get", return_value=opportunity), patch("product_intelligence.services.product_idea_nightly_orchestrator.OpportunityAIRecommendationRunner.run_with_openai", return_value=recommendation) as recommend, patch("product_intelligence.services.comparable_price_study_completion.ComparablePriceStudyCompletionService.run", return_value={"status": "integrated", "integrated": 1}) as complete:
            result = ProductIdeaNightlyOrchestratorService.run(idea_id=idea.pk, selection_service=selection, analysis_service=analysis)
        self.assertEqual(result["failures"], [])
        complete.assert_called_once()
        self.assertEqual(recommend.call_count, 2)
