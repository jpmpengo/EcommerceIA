from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.comparable_price_collection_runner import (
    ComparablePriceCollectionRunner,
)


class ComparablePriceCollectionRunnerTests(
    SimpleTestCase
):

    def test_processes_every_offer_through_research_pipeline(
        self,
    ):
        first_offer = Mock()
        second_offer = Mock()
        third_offer = Mock()

        product_idea = Mock()
        product_idea.supplier_offers.all.return_value = [
            first_offer,
            second_offer,
            third_offer,
        ]

        research_pipeline = Mock()
        research_pipeline.process.side_effect = [
            {
                "status": "researched",
                "delivery_status": "accepted",
                "comparable_prices_saved": 2,
            },
            {
                "status": "rejected",
                "delivery_status": "rejected",
                "comparable_prices_saved": 0,
            },
            {
                "status": "researched",
                "delivery_status": "slow",
                "comparable_prices_saved": 1,
            },
        ]

        qualification_service = Mock()
        qualification_service.qualify.side_effect = [
            {"examined": 2, "retained": 2, "rejected": 0},
            {"examined": 1, "retained": 1, "rejected": 0},
        ]

        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
            qualification_service=qualification_service,
            destination_country="FR",
        )

        summary = runner.run(
            product_idea=product_idea
        )

        self.assertEqual(
            research_pipeline.process.call_count,
            3,
        )

        research_pipeline.process.assert_any_call(
            supplier_offer=first_offer,
            destination_country="FR",
        )

        self.assertEqual(
            summary,
            {
                "offers_processed": 3,
                "offers_researched": 2,
                "offers_incomplete": 0,
                "offers_rejected": 1,
                "offers_slow": 1,
                "offers_fallback": 0,
                "comparable_prices_saved": 3,
                "comparable_prices_examined": 3,
                "comparable_prices_retained": 3,
                "comparable_prices_rejected": 0,
            },
        )

        self.assertEqual(
            qualification_service.qualify.call_count,
            2,
        )

    def test_accepts_category_without_supplier_offers(
        self,
    ):
        product_idea = Mock()
        product_idea.supplier_offers.all.return_value = []

        research_pipeline = Mock()

        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
        )

        summary = runner.run(
            product_idea=product_idea
        )

        research_pipeline.process.assert_not_called()

        self.assertEqual(
            summary,
            {
                "offers_processed": 0,
                "offers_researched": 0,
                "offers_incomplete": 0,
                "offers_rejected": 0,
                "offers_slow": 0,
                "offers_fallback": 0,
                "comparable_prices_saved": 0,
                "comparable_prices_examined": 0,
                "comparable_prices_retained": 0,
                "comparable_prices_rejected": 0,
            },
        )

    def test_processes_offer_returned_by_fallback_service(self):
        eu_offer = Mock()
        cn_offer = Mock()
        product_idea = Mock()
        product_idea.supplier_offers.all.return_value = [eu_offer]

        research_pipeline = Mock()
        research_pipeline.process.side_effect = [
            {"status": "incomplete", "delivery_status": "incomplete", "comparable_prices_saved": 0},
            {"status": "researched", "delivery_status": "accepted", "comparable_prices_saved": 2},
        ]

        qualification_service = Mock()
        qualification_service.qualify.return_value = {
            "examined": 2, "retained": 2, "rejected": 0,
        }

        fallback_service = Mock()
        fallback_service.run.return_value = [cn_offer]

        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
            qualification_service=qualification_service,
            destination_country="FR",
            fallback_service=fallback_service,
        )

        summary = runner.run(product_idea=product_idea)

        self.assertEqual(research_pipeline.process.call_count, 2)
        research_pipeline.process.assert_any_call(
            supplier_offer=cn_offer,
            destination_country="FR",
        )
        self.assertEqual(summary["offers_processed"], 2)
        self.assertEqual(summary["offers_researched"], 1)
        self.assertEqual(summary["offers_incomplete"], 1)

    def test_skips_visually_rejected_offer(self):
        rejected_offer = Mock()
        rejected_offer.visual_match_classification = "rejected"

        accepted_offer = Mock()
        accepted_offer.visual_match_classification = "probable"

        product_idea = Mock()
        product_idea.supplier_offers.all.return_value = [
            rejected_offer,
            accepted_offer,
        ]

        research_pipeline = Mock()
        research_pipeline.process.return_value = {
            "status": "researched",
            "delivery_status": "accepted",
            "comparable_prices_saved": 0,
        }

        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
        )

        summary = runner.run(
            product_idea=product_idea,
        )

        research_pipeline.process.assert_called_once_with(
            supplier_offer=accepted_offer,
            destination_country="FR",
        )
        self.assertEqual(
            summary["offers_processed"],
            1,
        )

    def test_skips_offer_without_visual_result_when_idea_has_visual_references(self):
        unchecked_offer = Mock()
        unchecked_offer.visual_match_classification = ""

        accepted_offer = Mock()
        accepted_offer.visual_match_classification = "strong"

        product_idea = Mock()
        product_idea.visual_references.exists.return_value = True
        product_idea.supplier_offers.all.return_value = [
            unchecked_offer,
            accepted_offer,
        ]

        research_pipeline = Mock()
        research_pipeline.process.return_value = {
            "status": "researched",
            "delivery_status": "accepted",
            "comparable_prices_saved": 0,
        }

        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
        )

        summary = runner.run(product_idea=product_idea)

        research_pipeline.process.assert_called_once_with(
            supplier_offer=accepted_offer,
            destination_country="FR",
        )
        self.assertEqual(summary["offers_processed"], 1)

    def test_archives_current_prices_for_visually_rejected_offer(self):
        rejected_offer = Mock()
        rejected_offer.visual_match_classification = "rejected"

        product_idea = Mock()
        product_idea.visual_references.exists.return_value = True
        product_idea.supplier_offers.all.return_value = [rejected_offer]

        research_pipeline = Mock()
        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
        )

        runner.run(product_idea=product_idea)

        research_pipeline.process.assert_not_called()
        rejected_offer.comparable_prices.filter.assert_called_once_with(
            is_current=True,
        )
        rejected_offer.comparable_prices.filter.return_value.update.assert_called_once_with(
            is_current=False,
        )

    def test_archives_current_prices_for_unchecked_offer_when_visual_references_exist(self):
        unchecked_offer = Mock()
        unchecked_offer.visual_match_classification = ""

        product_idea = Mock()
        product_idea.visual_references.exists.return_value = True
        product_idea.supplier_offers.all.return_value = [unchecked_offer]

        research_pipeline = Mock()
        runner = ComparablePriceCollectionRunner(
            research_pipeline=research_pipeline,
        )

        runner.run(product_idea=product_idea)

        research_pipeline.process.assert_not_called()
        unchecked_offer.comparable_prices.filter.assert_called_once_with(
            is_current=True,
        )
        unchecked_offer.comparable_prices.filter.return_value.update.assert_called_once_with(
            is_current=False,
        )

    def test_classifies_retained_comparables_after_qualification(self):
        offer = Mock()
        offer.visual_match_classification = 'strong'
        comparable = Mock()
        offer.comparable_prices.filter.return_value = [comparable]
        idea = Mock()
        idea.supplier_offers.all.return_value = [offer]
        research = Mock()
        research.process.return_value = {'status': 'researched', 'comparable_prices_saved': 1}
        qualification = Mock()
        qualification.qualify.return_value = {'examined': 1, 'retained': 1, 'rejected': 0}
        classification = Mock()
        runner = ComparablePriceCollectionRunner(research_pipeline=research, qualification_service=qualification, commercial_classification_service=classification)
        runner.run(idea)
        qualification.qualify.assert_called_once_with(offer)
        offer.comparable_prices.filter.assert_called_once_with(is_current=True, qualification_status='retained')
        classification.classify_and_save.assert_called_once_with(offer, [comparable])
