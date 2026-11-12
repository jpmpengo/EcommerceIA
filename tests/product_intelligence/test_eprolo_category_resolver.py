from django.test import SimpleTestCase

from product_intelligence.services.eprolo_category_resolver import (
    EproloCategoryResolver,
)


class EproloCategoryResolverTests(SimpleTestCase):

    def setUp(self):
        self.resolver = EproloCategoryResolver()

    def test_resolves_supported_selected_ideas(self):
        self.assertEqual(
            self.resolver.resolve("urban gardening planter"),
            {"ware_type_id": 15, "ware_type_two_id": 134},
        )
        self.assertEqual(
            self.resolver.resolve("accessoires vélo bicycle light"),
            {"ware_type_id": 26, "ware_type_two_id": 67},
        )
        self.assertEqual(
            self.resolver.resolve("laptop desk workspace"),
            {"ware_type_id": 13, "ware_type_two_id": 126},
        )

    def test_refuses_unknown_category(self):
        self.assertIsNone(
            self.resolver.resolve("unclassified product")
        )
