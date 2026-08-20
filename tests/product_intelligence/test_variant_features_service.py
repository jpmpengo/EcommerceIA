from django.test import SimpleTestCase

from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)


class VariantFeaturesServiceTests(SimpleTestCase):

    def test_extracts_printful_dimensions_in_mm(
        self,
    ):
        service = VariantFeaturesService()

        variant = {
            "name": (
                "Gaming Mouse Pad "
                "(White / 36″×18″)"
            ),
            "size": "36″×18″",
            "color": "White",
        }

        features = service.extract(
            variant=variant,
        )

        self.assertEqual(
            features["dimensions_mm"],
            (914, 457),
        )

        self.assertEqual(
            features["color"],
            "White",
        )

    def test_extracts_cj_dimensions_and_color(
        self,
    ):
        service = VariantFeaturesService()

        variant = {
            "variantNameEn": (
                "Competitive Gaming Office "
                "Waterproof Mouse Pad "
                "Black 80x40x2cm"
            ),
        }

        features = service.extract(
            variant=variant,
        )

        self.assertEqual(
            features["dimensions_mm"],
            (800, 400),
        )

        self.assertEqual(
            features["color"],
            "Black",
        )

    def test_extracts_dimensions_with_in_unit(
        self,
    ):
        service = VariantFeaturesService()

        features = service.extract(
            variant={
                "name": (
                    "Cotton Canvas Tote Bag "
                    "15 x 16 in"
                ),
            }
        )

        self.assertEqual(
            features["dimensions_mm"],
            (
                381,
                406,
            ),
        )

    def test_extracts_dimensions_from_html_encoded_inches(
        self,
    ):
        service = VariantFeaturesService()

        features = service.extract(
            variant={
                "name": (
                    "Cotton Canvas Tote Bag "
                    "15&quot; x 16&quot;"
                ),
            }
        )

        self.assertEqual(
            features["dimensions_mm"],
            (
                381,
                406,
            ),
        )

    def test_extracts_mug_capacity_from_ounces(
        self,
    ):
        service = VariantFeaturesService()

        features = service.extract(
            variant={
                "name": (
                    "White Ceramic Mug 11 oz"
                ),
            }
        )

        self.assertEqual(
            features["capacity_ml"],
            325,
        )

    def test_extracts_mug_capacity_from_milliliters(
        self,
    ):
        service = VariantFeaturesService()

        features = service.extract(
            variant={
                "variantNameEn": (
                    "Ceramic Coffee Mug 200ml"
                ),
            }
        )

        self.assertEqual(
            features["capacity_ml"],
            200,
        )
