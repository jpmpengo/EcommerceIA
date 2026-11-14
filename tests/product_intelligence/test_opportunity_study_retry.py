from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch, Mock
from django.test import SimpleTestCase
from django.utils import timezone
from product_intelligence.services.opportunity_study_completion import OpportunityStudyCompletionService

class OpportunityStudyRetryTests(SimpleTestCase):
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
