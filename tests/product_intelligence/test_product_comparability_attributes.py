from django.test import SimpleTestCase

from product_intelligence.services.product_comparability_attributes import (
    ProductComparabilityAttributesService,
)


class ProductComparabilityAttributesServiceTests(SimpleTestCase):

    def test_extracts_leading_pack_quantity(self):
        result = ProductComparabilityAttributesService().extract(
            "3 high waist physiological pants XL"
        )
        self.assertEqual(result["pack_quantity"], 3)
        self.assertEqual(result["size"], "XL")

    def test_extracts_set_quantity_and_dimensions(self):
        result = ProductComparabilityAttributesService().extract(
            "Set of 5 resistance bands 20 x 30 cm"
        )
        self.assertEqual(result["pack_quantity"], 5)
        self.assertEqual(result["dimensions_mm"], (200, 300))

    def test_extracts_macrame_hanger_without_pot(self):
        result = ProductComparabilityAttributesService().extract("Macrame Pot Holder - Large Pot Holder - Extra Long", evidence="Macrame plant hangers. Plant and pot in picture not included.")
        self.assertEqual(result["product_family"], "macrame_hanger")
        self.assertFalse(result["includes_pot"])


    def test_does_not_treat_leading_lumens_as_pack_quantity(self):
        result = ProductComparabilityAttributesService().extract(
            "350 Lumens USB Rechargeable Bicycle Light Set 4 Modes Front Headlight And Rear Taillight"
        )
        self.assertIsNone(result["pack_quantity"])
