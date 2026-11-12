from django.test import SimpleTestCase

from product_intelligence.services.demand_score_service import DemandScoreService


class DemandScoreServiceTests(SimpleTestCase):

    def test_no_qualified_signal_returns_zero(self):
        score = DemandScoreService.calculate([])

        self.assertEqual(score, 0)

    def test_direct_signal_scores_higher_than_contextual_signal(self):
        direct_score = DemandScoreService.calculate([{"type": "direct"}])
        contextual_score = DemandScoreService.calculate([{"type": "contextual"}])

        self.assertGreater(direct_score, contextual_score)

    def test_signal_types_follow_demand_strength_order(self):
        direct = DemandScoreService.calculate([{"type": "direct"}])
        trend = DemandScoreService.calculate([{"type": "trend"}])
        need = DemandScoreService.calculate([{"type": "need"}])
        contextual = DemandScoreService.calculate([{"type": "contextual"}])

        self.assertGreater(direct, trend)
        self.assertGreater(trend, need)
        self.assertGreater(need, contextual)

    def test_multiple_signals_strengthen_score_without_exceeding_one_hundred(self):
        single_trend = DemandScoreService.calculate([{"type": "trend"}])
        combined = DemandScoreService.calculate([
            {"type": "need"},
            {"type": "trend"},
        ])

        self.assertGreater(combined, single_trend)
        self.assertLessEqual(combined, 100)

    def test_mixed_realistic_signals_return_expected_score(self):
        score = DemandScoreService.calculate([
            {"type": "trend"},
            {"type": "need"},
            {"type": "contextual"},
        ])

        self.assertEqual(score, 93)

    def test_target_market_signal_scores_higher_than_precursor_signal(self):
        target_score = DemandScoreService.calculate([{"type": "direct", "markets": ["FR"], "role": "target_market"}])
        precursor_score = DemandScoreService.calculate([{"type": "direct", "markets": ["US"], "role": "precursor"}])

        self.assertGreater(target_score, precursor_score)
