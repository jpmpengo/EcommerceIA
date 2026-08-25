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

        service = (
            SupplierCandidateCollectionService(
                search_service=search_service,
            )
        )

        summary = service.collect(
            product_idea=idea,
        )

        search_service.search_for_idea.assert_called_once_with(
            product_idea=idea,
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