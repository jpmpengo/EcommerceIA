from django.test import TestCase

from product_intelligence.models import (
    MarketplaceStudy,
    ProductIdea,
)


class MarketplaceStudyModelTests(TestCase):

    def test_study_belongs_to_selected_product_idea(
        self,
    ):
        idea = ProductIdea.objects.create(
            name="Organisateur sous évier",
            customer_problem=(
                "Le rangement est difficile "
                "autour de la plomberie."
            ),
            target_customer=(
                "Habitants de petits logements."
            ),
            reason_to_study=(
                "Le besoin est concret."
            ),
            countries=[
                "FR",
                "BE",
                "ES",
            ],
            search_keywords=[
                "organisateur sous évier",
                "rangement sous évier cuisine",
            ],
            status="selected",
        )

        study = MarketplaceStudy.objects.create(
            product_idea=idea,
            marketplaces=[
                "amazon",
                "etsy",
            ],
            queries=[
                "organisateur sous évier",
                "rangement sous évier cuisine",
            ],
        )

        self.assertEqual(
            study.product_idea,
            idea,
        )

        self.assertEqual(
            study.status,
            "draft",
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
            list(
                idea.marketplace_studies.all()
            ),
            [
                study,
            ],
        )