from unittest.mock import Mock

from django.test import SimpleTestCase

from product_intelligence.services.supplier_candidate_collection import (
    SupplierCandidateCollectionService,
)


class SupplierCandidateCollectionServiceTests(
    SimpleTestCase
):

    def test_collects_candidates_and_returns_technical_summary(
        self,
    ):
        idea = Mock()
        idea.id = 42
        idea.status = "selected"

        cj_offer_1 = Mock()
        cj_offer_1.supplier.name = (
            "CJdropshipping"
        )

        cj_offer_2 = Mock()
        cj_offer_2.supplier.name = (
            "CJdropshipping"
        )

        printful_offer = Mock()
        printful_offer.supplier.name = (
            "Printful"
        )

        search_service = Mock()
        search_service.supplier_searchers = [
            Mock(),
            Mock(),
        ]
        search_service.search_for_idea.return_value = [
            cj_offer_1,
            cj_offer_2,
            printful_offer,
        ]
        search_service.supplier_failures = {
            "AW Dropship": "HTTP 403",
        }

        visual_matching_service = Mock()

        service = (
            SupplierCandidateCollectionService(
                search_service=search_service,
                visual_matching_service=(
                    visual_matching_service
                ),
            )
        )

        summary = service.collect(
            product_idea=idea,
        )

        search_service.search_for_idea.assert_called_once_with(
            product_idea=idea,
        )

        visual_matching_service.match.assert_called_once_with(
            [
                cj_offer_1,
                cj_offer_2,
                printful_offer,
            ]
        )

        self.assertEqual(
            summary,
            {
                "product_idea_id": 42,
                "suppliers_searched": 2,
                "offers_found": 3,
                "offers_by_supplier": {
                    "CJdropshipping": 2,
                    "Printful": 1,
                },
                "suppliers_unavailable": {
                    "AW Dropship": "HTTP 403",
                },
            },
        )

    def test_rejects_unselected_product_idea(
        self,
    ):
        idea = Mock()
        idea.status = "proposed"

        search_service = Mock()

        service = (
            SupplierCandidateCollectionService(
                search_service=search_service,
            )
        )

        with self.assertRaisesMessage(
            ValueError,
            (
                "La catégorie doit être "
                "sélectionnée avant la "
                "recherche fournisseur."
            ),
        ):
            service.collect(
                product_idea=idea,
            )

        search_service.search_for_idea.assert_not_called()
    def test_collects_candidates_for_validated_product_idea(self):
        idea = Mock()
        idea.id = 43
        idea.status = "validated"
        search_service = Mock()
        search_service.supplier_searchers = []
        search_service.search_for_idea.return_value = []
        service = SupplierCandidateCollectionService(search_service=search_service)
        summary = service.collect(product_idea=idea)
        search_service.search_for_idea.assert_called_once_with(product_idea=idea)
        self.assertEqual(summary["product_idea_id"], 43)

    def test_uses_cn_fallback_when_no_eu_offer_is_found(self):
        idea = Mock()
        idea.id = 44
        idea.status = "selected"

        cn_offer_1 = Mock()
        cn_offer_1.supplier.name = "CJdropshipping"
        cn_offer_2 = Mock()
        cn_offer_2.supplier.name = "CJdropshipping"

        search_service = Mock()
        search_service.supplier_searchers = [Mock()]
        search_service.search_for_idea.return_value = []
        search_service.supplier_failures = {}

        fallback_service = Mock()
        fallback_service.run.return_value = [cn_offer_1, cn_offer_2]

        visual_matching_service = Mock()

        service = SupplierCandidateCollectionService(
            search_service=search_service,
            visual_matching_service=visual_matching_service,
            fallback_service=fallback_service,
        )

        summary = service.collect(product_idea=idea)

        fallback_service.run.assert_called_once_with(
            product_idea=idea,
            eu_offer_results=[],
        )
        visual_matching_service.match.assert_called_once_with(
            [cn_offer_1, cn_offer_2]
        )
        self.assertEqual(summary["offers_found"], 2)
        self.assertEqual(
            summary["offers_by_supplier"],
            {"CJdropshipping": 2},
        )
