from unittest.mock import Mock

from django.test import TestCase

from product_intelligence.services.cj_economic_fallback import (
    CJEconomicFallbackService,
)


class CJEconomicFallbackServiceTests(TestCase):

    def test_searches_cn_and_returns_only_researched_offers(self):
        idea = Mock()
        researched_offer = Mock()
        rejected_offer = Mock()

        cj_searcher = Mock()
        cj_searcher.search_for_idea_in_country.return_value = [
            researched_offer,
            rejected_offer,
        ]

        research_pipeline = Mock()
        research_pipeline.process.side_effect = [
            {
                "status": "researched",
            },
            {
                "status": "rejected",
            },
        ]

        qualification_service = Mock()
        qualification_service.qualify.return_value = {
            "examined": 5,
            "retained": 4,
            "rejected": 1,
        }

        service = CJEconomicFallbackService(
            cj_searcher=cj_searcher,
            research_pipeline=research_pipeline,
            qualification_service=qualification_service,
            destination_country="FR",
        )

        result = service.run(
            product_idea=idea,
        )

        cj_searcher.search_for_idea_in_country.assert_called_once_with(
            product_idea=idea,
            country_code="CN",
        )

        research_pipeline.process.assert_any_call(
            supplier_offer=researched_offer,
            destination_country="FR",
        )
        research_pipeline.process.assert_any_call(
            supplier_offer=rejected_offer,
            destination_country="FR",
        )

        qualification_service.qualify.assert_called_once_with(
            researched_offer,
        )

        self.assertEqual(
            result,
            [researched_offer],
        )

    def test_rejected_visual_match_does_not_reach_research_pipeline(self):
        product_idea = Mock()
        rejected_offer = Mock(id=296)
        rejected_offer.visual_match_classification = "rejected"
        accepted_offer = Mock(id=301)
        accepted_offer.visual_match_classification = "probable"

        cj_searcher = Mock()
        cj_searcher.search_for_idea_in_country.return_value = [
            rejected_offer,
            accepted_offer,
        ]

        visual_matching_service = Mock()
        visual_matching_service.match.return_value = {
            "matches": []
        }

        research_pipeline = Mock()
        research_pipeline.process.return_value = {
            "status": "researched",
        }

        service = CJEconomicFallbackService(
            cj_searcher=cj_searcher,
            research_pipeline=research_pipeline,
            visual_matching_service=visual_matching_service,
        )

        result = service.run(
            product_idea=product_idea,
        )

        visual_matching_service.match.assert_called_once_with([
            rejected_offer,
            accepted_offer,
        ])
        research_pipeline.process.assert_called_once_with(
            supplier_offer=accepted_offer,
            destination_country="FR",
        )
        self.assertEqual(result, [accepted_offer])

    def test_unchecked_visual_offer_does_not_reach_research_pipeline(self):
        product_idea = Mock()
        product_idea.visual_references.exists.return_value = True

        unchecked_offer = Mock(id=302)
        unchecked_offer.visual_match_classification = ""

        accepted_offer = Mock(id=303)
        accepted_offer.visual_match_classification = "strong"

        cj_searcher = Mock()
        cj_searcher.search_for_idea_in_country.return_value = [
            unchecked_offer,
            accepted_offer,
        ]

        visual_matching_service = Mock()
        visual_matching_service.match.return_value = {"matches": []}

        research_pipeline = Mock()
        research_pipeline.process.return_value = {
            "status": "researched",
        }

        service = CJEconomicFallbackService(
            cj_searcher=cj_searcher,
            research_pipeline=research_pipeline,
            visual_matching_service=visual_matching_service,
        )

        result = service.run(product_idea=product_idea)

        research_pipeline.process.assert_called_once_with(
            supplier_offer=accepted_offer,
            destination_country="FR",
        )
        self.assertEqual(result, [accepted_offer])
