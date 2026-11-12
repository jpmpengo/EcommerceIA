from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.cj_country_fallback import (
    CJCountryFallbackService,
)


class CJCountryFallbackServiceTests(SimpleTestCase):

    def test_searches_cn_when_no_eu_offer_is_usable(self):
        idea = Mock()
        cj_searcher = Mock()
        cj_searcher.search_for_idea_in_country.return_value = ["CN-OFFER"]

        service = CJCountryFallbackService(cj_searcher=cj_searcher)

        result = service.run(
            product_idea=idea,
            eu_offer_results=[
                {"status": "incomplete"},
                {"status": "rejected"},
            ],
        )

        cj_searcher.search_for_idea_in_country.assert_called_once_with(
            product_idea=idea,
            country_code="CN",
        )
        self.assertEqual(result, ["CN-OFFER"])

    def test_does_not_search_cn_when_eu_offer_is_usable(self):
        idea = Mock()
        cj_searcher = Mock()
        service = CJCountryFallbackService(cj_searcher=cj_searcher)

        result = service.run(
            product_idea=idea,
            eu_offer_results=[
                {"status": "incomplete"},
                {"status": "researched"},
            ],
        )

        cj_searcher.search_for_idea_in_country.assert_not_called()
        self.assertEqual(result, [])

    def test_does_not_search_cn_when_eu_offer_is_usable(self):
        idea = Mock()
        cj_searcher = Mock()
        service = CJCountryFallbackService(cj_searcher=cj_searcher)

        result = service.run(
            product_idea=idea,
            eu_offer_results=[
                {"status": "incomplete"},
                {"status": "researched"},
            ],
        )

        cj_searcher.search_for_idea_in_country.assert_not_called()
        self.assertEqual(result, [])

    def test_searches_cn_when_eu_results_are_empty(self):
        idea = Mock()
        cj_searcher = Mock()
        cj_searcher.search_for_idea_in_country.return_value = ["CN-OFFER"]
        service = CJCountryFallbackService(cj_searcher=cj_searcher)

        result = service.run(
            product_idea=idea,
            eu_offer_results=[],
        )

        cj_searcher.search_for_idea_in_country.assert_called_once_with(
            product_idea=idea,
            country_code="CN",
        )
        self.assertEqual(result, ["CN-OFFER"])
