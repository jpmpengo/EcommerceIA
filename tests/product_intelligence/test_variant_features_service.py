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
