from django.test import SimpleTestCase

from product_intelligence.services.competition_score_service import CompetitionScoreService


class CompetitionScoreServiceTests(SimpleTestCase):

    def test_returns_zero_when_market_evidence_is_insufficient(self):
        score = CompetitionScoreService.calculate({
            "retained_count": 2,
            "source_domain_count": 1,
            "minimum_price": None,
            "median_price": None,
            "maximum_price": None,
        })

        self.assertEqual(score, 0)

    def test_more_source_domains_increase_competition_score(self):
        low = CompetitionScoreService.calculate({
            "retained_count": 3,
            "source_domain_count": 2,
            "minimum_price": 10,
            "median_price": 20,
            "maximum_price": 30,
        })
        high = CompetitionScoreService.calculate({
            "retained_count": 5,
            "source_domain_count": 5,
            "minimum_price": 10,
            "median_price": 20,
            "maximum_price": 30,
        })

        self.assertGreater(high, low)

    def test_source_domain_scale_is_explicit(self):
        self.assertEqual(CompetitionScoreService.calculate({"retained_count": 3, "source_domain_count": 2}), 25)
        self.assertEqual(CompetitionScoreService.calculate({"retained_count": 3, "source_domain_count": 3}), 50)
        self.assertEqual(CompetitionScoreService.calculate({"retained_count": 4, "source_domain_count": 4}), 75)
        self.assertEqual(CompetitionScoreService.calculate({"retained_count": 5, "source_domain_count": 5}), 100)

    def test_tighter_prices_increase_competition_score_for_same_source_count(self):
        tight = CompetitionScoreService.calculate({"retained_count": 5, "source_domain_count": 4, "minimum_price": 18, "median_price": 20, "maximum_price": 22})
        dispersed = CompetitionScoreService.calculate({"retained_count": 5, "source_domain_count": 4, "minimum_price": 10, "median_price": 20, "maximum_price": 40})

        self.assertGreater(tight, dispersed)
