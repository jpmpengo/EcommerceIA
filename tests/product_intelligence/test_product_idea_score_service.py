from datetime import date

from django.test import SimpleTestCase

from product_intelligence.services.product_idea_score_service import (
    ProductIdeaScoreService,
)


class ProductIdeaScoreServiceTests(SimpleTestCase):

    def test_calculate_for_idea_uses_idea_demand_signal_assessments(self):
        class FakeIdea:
            demand_signal_assessments = [
                {
                    "type": "trend",
                    "markets": ["US", "JP"],
                    "role": "precursor",
                    "strength": "strong",
                    "metric": "search_trend", "is_verified": True,
                    "value": "documented growth",
                    "source_url": "https://example.com/source",
                    "observed_at": "2026-09-20",
                }
            ]

        score = ProductIdeaScoreService.calculate_for_idea(
            FakeIdea(),
            reference_date="2026-09-27",
        )

        self.assertEqual(score, 90)


    def test_calculate_accepts_observed_at_as_date(self):
        score = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/source",
                "observed_at": date(2026, 9, 20),
            }
        ], reference_date=date(2026, 9, 27))

        self.assertEqual(score, 85)

    def test_no_signal_returns_zero(self):
        score = ProductIdeaScoreService.calculate([])

        self.assertEqual(score, 0)

    def test_low_local_saturation_scores_higher_than_high_saturation(self):
        signals = [
            {
                "type": "trend",
                "markets": ["US", "JP"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/source",
                "observed_at": "2026-09-20",
            }
        ]

        low = ProductIdeaScoreService.calculate(
            signals,
            reference_date="2026-09-27",
            local_saturation="low",
        )

        high = ProductIdeaScoreService.calculate(
            signals,
            reference_date="2026-09-27",
            local_saturation="high",
        )

        self.assertGreater(low, high)

    def test_direct_precursor_scores_higher_than_need_at_same_strength(self):
        direct = ProductIdeaScoreService.calculate([
            {
                "type": "direct",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "reviews",
                "value": "documented purchases and reviews",
                "source_url": "https://example.com/direct",
                "observed_at": "2026-09-20",
            }
        ], reference_date="2026-09-28")

        need = ProductIdeaScoreService.calculate([
            {
                "type": "need",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "adoption",
                "value": "documented customer need",
                "source_url": "https://example.com/need",
                "observed_at": "2026-09-20",
            }
        ], reference_date="2026-09-28")

        self.assertGreater(direct, need)

    def test_strong_precursor_signal_scores_higher_than_weak_precursor_signal(self):
        strong_score = ProductIdeaScoreService.calculate([
            {
                "type": "direct",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "sales",
                "value": "10000+ purchases",
                "source_url": "https://example.com/strong",
                "observed_at": "2026-09-25",
            }
        ])

        weak_score = ProductIdeaScoreService.calculate([
            {
                "type": "direct",
                "markets": ["US"],
                "role": "precursor",
                "strength": "weak",
                "metric": "sales",
                "value": "limited evidence",
                "source_url": "https://example.com/weak",
                "observed_at": "2026-09-25",
            }
        ])

        self.assertGreater(strong_score, weak_score)

    def test_multiple_precursor_markets_strengthen_score(self):
        one_market = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/us",
                "observed_at": "2026-09-25",
            }
        ])

        multiple_markets = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US", "JP", "KR"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/multi",
                "observed_at": "2026-09-25",
            }
        ])

        self.assertGreater(multiple_markets, one_market)

    def test_recent_precursor_signal_scores_higher_than_old_signal(self):
        recent = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/recent",
                "observed_at": "2026-09-20",
            }
        ], reference_date="2026-09-27")

        old = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/old",
                "observed_at": "2025-09-20",
            }
        ], reference_date="2026-09-27")

        self.assertGreater(recent, old)

    def test_target_market_only_does_not_bonus_itself(self):
        score = ProductIdeaScoreService.calculate([
            {
                "type": "direct",
                "markets": ["FR"],
                "role": "target_market",
                "strength": "moderate",
                "metric": "adoption",
                "value": "documented local demand",
                "source_url": "https://example.com/fr",
                "observed_at": "2026-09-20",
            }
        ], reference_date="2026-09-27")

        self.assertLess(score, 50)

    def test_target_market_cannot_replace_precursor_as_base_score(self):
        score = ProductIdeaScoreService.calculate([
            {
                "type": "need",
                "markets": ["US"],
                "role": "precursor",
                "strength": "moderate",
                "metric": "adoption",
                "value": "documented precursor need",
                "source_url": "https://example.com/us",
                "observed_at": "2026-09-20",
            },
            {
                "type": "direct",
                "markets": ["FR"],
                "role": "target_market",
                "strength": "strong",
                "metric": "sales",
                "value": "strong local sales",
                "source_url": "https://example.com/fr",
                "observed_at": "2026-09-20",
            },
        ], reference_date="2026-09-28")

        self.assertLess(score, 75)

    def test_target_market_confirmation_strengthens_precursor_idea(self):
        precursor_only = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US", "JP"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/precursor",
                "observed_at": "2026-09-20",
            }
        ], reference_date="2026-09-27")

        precursor_and_target = ProductIdeaScoreService.calculate([
            {
                "type": "trend",
                "markets": ["US", "JP"],
                "role": "precursor",
                "strength": "strong",
                "metric": "search_trend", "is_verified": True,
                "value": "documented growth",
                "source_url": "https://example.com/precursor",
                "observed_at": "2026-09-20",
            },
            {
                "type": "need",
                "markets": ["FR"],
                "role": "target_market",
                "strength": "moderate",
                "metric": "adoption",
                "value": "documented local need",
                "source_url": "https://example.com/fr",
                "observed_at": "2026-09-20",
            }
        ], reference_date="2026-09-27")

        self.assertGreater(precursor_and_target, precursor_only)

    def test_emerging_growth_scores_higher_than_sales_volume(self):
        base = {"type": "direct", "markets": ["US"], "role": "precursor", "strength": "strong", "source_url": "https://example.com/source", "observed_at": "2026-09-25"}
        growth = dict(base, metric="search_trend", is_verified=True, value="documented recent growth")
        volume = dict(base, metric="sales", value="10000+ purchases")
        self.assertGreater(ProductIdeaScoreService.calculate([growth]), ProductIdeaScoreService.calculate([volume]))

    def test_no_growth_does_not_receive_growth_bonus(self):
        base = {"type": "trend", "markets": ["US"], "role": "precursor", "strength": "strong", "metric": "search_trend", "is_verified": True, "source_url": "https://example.com/source", "observed_at": "2026-09-25"}
        growing = dict(base, value="documented recent growth")
        stagnant = dict(base, value="no growth observed")
        self.assertGreater(ProductIdeaScoreService.calculate([growing]), ProductIdeaScoreService.calculate([stagnant]))

    def test_unverified_sales_growth_scores_zero(self):
        signal = {
            'type': 'direct',
            'markets': ['US'],
            'role': 'precursor',
            'strength': 'strong',
            'metric': 'sales_growth',
            'value': 'Sales rose 149%',
            'is_verified': False,
        }
        self.assertEqual(ProductIdeaScoreService.calculate([signal]), 0)

    def test_search_trend_without_verification_scores_zero(self):
        signal = dict(type='trend', markets=['US', 'JP'], role='precursor', strength='strong', metric='search_trend', value='documented growth')
        self.assertEqual(ProductIdeaScoreService.calculate([signal]), 0)
