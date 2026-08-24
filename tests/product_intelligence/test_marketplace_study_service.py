from django.test import TestCase

from product_intelligence.models import (
    ProductIdea,
)
from product_intelligence.services.marketplace_study import (
    MarketplaceStudyService,
)


class MarketplaceStudyServiceTests(TestCase):

    def test_prepare_creates_limited_study_for_selected_idea(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
                "rangement sous évier cuisine",
                "étagère sous évier réglable",
            ],
            status="selected",
        )

        study = MarketplaceStudyService.prepare(
            idea=idea,
            marketplaces=[
                "etsy",
                "woocommerce_local",
            ],
        )

        self.assertEqual(
            study.product_idea,
            idea,
        )

        self.assertEqual(
            study.marketplaces,
            [
                "etsy",
                "woocommerce_local",
            ],
        )

        self.assertEqual(
            study.queries,
            idea.search_keywords,
        )

        self.assertEqual(
            study.max_pages_per_marketplace,
            2,
        )

        self.assertEqual(
            study.max_results_per_query,
            20,
        )

        self.assertEqual(
            study.status,
            "draft",
        )

    def test_prepare_reuses_existing_draft_study(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem="Rangement difficile.",
            target_customer="Petits logements.",
            reason_to_study="Besoin concret.",
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
            ],
            status="selected",
        )

        first_study = (
            MarketplaceStudyService
            .prepare(
                idea=idea,
                marketplaces=[
                    "etsy",
                ],
            )
        )

        second_study = (
            MarketplaceStudyService
            .prepare(
                idea=idea,
                marketplaces=[
                    "etsy",
                ],
            )
        )

        self.assertEqual(
            first_study.pk,
            second_study.pk,
        )

        self.assertEqual(
            idea.marketplace_studies.count(),
            1,
        )

    def test_prepare_rejects_more_than_two_marketplaces(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Idée sélectionnée",
            customer_problem="Problème.",
            target_customer="Client.",
            reason_to_study="Raison.",
            countries=[
                "FR",
            ],
            search_keywords=[
                "requête ciblée",
            ],
            status="selected",
        )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Deux marketplaces maximum "
                "sont autorisées."
            ),
        ):
            MarketplaceStudyService.prepare(
                idea=idea,
                marketplaces=[
                    "etsy",
                    "woocommerce_local",
                    "amazon",
                ],
            )

        self.assertEqual(
            idea.marketplace_studies.count(),
            0,
        )

    def test_prepare_rejects_unselected_idea(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Idée non sélectionnée",
            customer_problem="Problème.",
            target_customer="Client.",
            reason_to_study="Raison.",
            countries=[
                "FR",
            ],
            search_keywords=[
                "requête ciblée",
            ],
            status="proposed",
        )

        with self.assertRaisesMessage(
            ValueError,
            (
                "Seule une idée sélectionnée "
                "peut être étudiée."
            ),
        ):
            MarketplaceStudyService.prepare(
                idea=idea,
                marketplaces=[
                    "etsy",
                ],
            )

        self.assertEqual(
            idea.marketplace_studies.count(),
            0,
        )

    def test_prepare_rejects_unsupported_marketplace(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Idée sélectionnée",
            customer_problem="Problème.",
            target_customer="Client.",
            reason_to_study="Raison.",
            countries=[
                "FR",
            ],
            search_keywords=[
                "requête ciblée",
            ],
            status="selected",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Marketplace non autorisée : amazon.",
        ):
            MarketplaceStudyService.prepare(
                idea=idea,
                marketplaces=[
                    "amazon",
                ],
            )

        self.assertEqual(
            idea.marketplace_studies.count(),
            0,
        )