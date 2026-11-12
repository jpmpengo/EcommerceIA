from io import StringIO
from unittest.mock import patch

from django.core.management import (
    call_command,
)
from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)
from django.core.management.base import (
    CommandError,
)

class CollectSupplierCandidatesCommandTests(
    TestCase
):

    @patch(
        (
            "product_intelligence.management."
            "commands.collect_supplier_candidates."
            "SupplierCandidateCollectionRunner."
            "collect"
        )
    )
    def test_collects_candidates_for_selected_idea(
        self,
        collect,
    ):
        idea = ProductIdea.objects.create(
            name=(
                "Accessoires de bureau "
                "ergonomiques"
            ),
            customer_problem=(
                "Améliorer le confort de travail."
            ),
            target_customer=(
                "Télétravailleurs européens."
            ),
            reason_to_study=(
                "Catégorie soutenue par "
                "des signaux publics."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "accessoire bureau ergonomique",
            ],
            demand_signals=[
                "Intérêt public documenté.",
            ],
            evidence_sources=[
                {
                    "title": "Source publique",
                    "url": (
                        "https://example.com/source"
                    ),
                    "evidence": (
                        "La source décrit la demande."
                    ),
                },
            ],
            status="selected",
        )

        collect.return_value = {
            "product_idea_id": idea.id,
            "suppliers_searched": 2,
            "offers_found": 8,
            "offers_by_supplier": {
                "CJdropshipping": 5,
                "Printful": 3,
            },
        }

        output = StringIO()

        call_command(
            "collect_supplier_candidates",
            idea.id,
            stdout=output,
        )

        collect.assert_called_once_with(
            product_idea=idea,
        )

        rendered_output = (
            output.getvalue()
        )

        self.assertIn(
            "2 fournisseur(s) interrogé(s)",
            rendered_output,
        )

        self.assertIn(
            "8 offre(s) candidate(s)",
            rendered_output,
        )

        self.assertIn(
            "CJdropshipping : 5",
            rendered_output,
        )

        self.assertIn(
            "Printful : 3",
            rendered_output,
        )

    @patch(
        (
            "product_intelligence.management."
            "commands.collect_supplier_candidates."
            "SupplierCandidateCollectionRunner."
            "collect"
        )
    )
    def test_rejects_unselected_idea_before_collection(
        self,
        collect,
    ):
        idea = ProductIdea.objects.create(
            name="Catégorie non sélectionnée",
            customer_problem="Problème client.",
            target_customer="Client européen.",
            reason_to_study=(
                "Hypothèse encore à examiner."
            ),
            countries=[
                "FR",
            ],
            search_keywords=[
                "catégorie test",
            ],
            status="proposed",
        )

        with self.assertRaisesMessage(
            CommandError,
            (
                "La catégorie doit être "
                "sélectionnée."
            ),
        ):
            call_command(
                "collect_supplier_candidates",
                idea.id,
            )

        collect.assert_not_called()
    @patch(
        (
            "product_intelligence.management."
            "commands.collect_supplier_candidates."
            "SupplierCandidateCollectionRunner."
            "collect"
        )
    )
    def test_collects_candidates_for_validated_idea(
        self,
        collect,
    ):
        idea = ProductIdea.objects.create(
            name="Categorie validee",
            customer_problem="Probleme client.",
            target_customer="Client europeen.",
            reason_to_study="Categorie validee.",
            countries=["FR"],
            search_keywords=["categorie test"],
            status="validated",
        )

        collect.return_value = {
            "product_idea_id": idea.id,
            "suppliers_searched": 0,
            "offers_found": 0,
            "offers_by_supplier": {},
        }

        call_command(
            "collect_supplier_candidates",
            idea.id,
        )

        collect.assert_called_once_with(
            product_idea=idea,
        )
