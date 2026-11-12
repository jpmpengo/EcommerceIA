from django.test import SimpleTestCase

from product_intelligence.services.eprolo_product_matching import (
    EproloProductMatchingService,
)


class EproloProductMatchingServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = EproloProductMatchingService()

    def test_accepts_two_significant_common_terms(self):
        self.assertTrue(
            self.service.is_relevant(
                product_name=(
                    "Resin Hanging Planter Elegant Ballerina Design"
                ),
                search_keyword="hanging railing planter",
            )
        )

    def test_rejects_only_one_common_term(self):
        self.assertFalse(
            self.service.is_relevant(
                product_name=(
                    "Spaceship gorilla outdoor garden lamp"
                ),
                search_keyword="balcony herb garden kit",
            )
        )

    def test_rejects_unrelated_product(self):
        self.assertFalse(
            self.service.is_relevant(
                product_name="Plant growth fertilizer stick",
                search_keyword="hanging railing planter",
            )
        )

    def test_rejects_product_missing_bike_anchor(self):
        self.assertFalse(
            self.service.is_relevant(
                product_name="USB Rechargeable Camping Light",
                search_keyword="USB rechargeable bike light",
            )
        )
