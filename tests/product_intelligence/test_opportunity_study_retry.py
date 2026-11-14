from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch, Mock
from django.test import TestCase
from django.utils import timezone
from product_intelligence.services.opportunity_study_completion import OpportunityStudyCompletionService

class OpportunityStudyRetryTests(TestCase):
    def test_recent_unresolved_study_is_deferred(self):
        blockers = [{"category": "demand", "blocker": "Preuves insuffisantes"}]
        previous = {"date": timezone.now().isoformat(), "requested_complements": blockers, "results": {"demand": {"status": "unresolved"}}}
        recommendation = SimpleNamespace(decision="study", study_blockers=blockers, completion_history=[previous])
        opportunity = SimpleNamespace(supplier_offer_id=1)
        with patch("product_intelligence.services.opportunity_demand_study_completion.OpportunityDemandStudyCompletionService.run") as search:
            result = OpportunityStudyCompletionService.run(opportunity, recommendation)
        self.assertEqual(result["status"], "retry_deferred")
        search.assert_not_called()

    def test_old_unresolved_study_is_retried(self):
        blockers = [{"category": "demand", "blocker": "Preuves insuffisantes"}]
        previous = {"date": (timezone.now() - timedelta(days=8)).isoformat(), "requested_complements": blockers, "results": {"demand": {"status": "unresolved"}}}
        recommendation = SimpleNamespace(decision="study", study_blockers=blockers, completion_history=[previous], save=Mock())
        opportunity = SimpleNamespace(status="review", supplier_offer_id=1)
        with patch("product_intelligence.services.opportunity_demand_study_completion.OpportunityDemandStudyCompletionService.run", return_value={"status": "unresolved"}) as search:
            result = OpportunityStudyCompletionService.run(opportunity, recommendation)
        search.assert_called_once_with(opportunity)

    def test_exhausted_critical_study_is_rejected(self):
        blockers = [{"category": "other", "blocker": "Conformite technique non demontree"}]
        history = [{"date": (timezone.now() - timedelta(days=8 * (3-i))).isoformat(), "requested_complements": blockers, "results": {"other": {"status": "unresolved", "verification_performed": True}}} for i in range(3)]
        recommendation = SimpleNamespace(decision="study", study_blockers=blockers, completion_history=history, summary="Etude en cours", merchant_summary="", save=Mock())
        opportunity = SimpleNamespace(status="review", supplier_offer_id=1, save=Mock())
        result = OpportunityStudyCompletionService.run(opportunity, recommendation)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(opportunity.status, "rejected")
        self.assertEqual(recommendation.decision, "reject")
        self.assertEqual(len(recommendation.completion_history), 4)

    def test_unverified_attempts_do_not_trigger_rejection(self):
        blockers = [{"category": "other", "blocker": "Conformite technique non demontree"}]
        history = [{"date": (timezone.now() - timedelta(days=8 * (3-i))).isoformat(), "requested_complements": blockers, "results": {"other": {"status": "unresolved"}}} for i in range(3)]
        recommendation = SimpleNamespace(decision="study", study_blockers=blockers, completion_history=history, save=Mock())
        opportunity = SimpleNamespace(status="review", supplier_offer_id=None, save=Mock())
        OpportunityStudyCompletionService.run(opportunity, recommendation)
        self.assertEqual(opportunity.status, "review")
        self.assertEqual(recommendation.decision, "study")
        opportunity.save.assert_not_called()
