from django.test import SimpleTestCase

from product_intelligence.services.supplier_product_matching import (
    SupplierProductMatchingService,
)


class SupplierProductMatchingServiceTests(
    SimpleTestCase
):

    def test_matches_similar_mouse_pad_names(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        cj_name = (
            "Large Mouse Pad, Gaming Gaming, "
            "Colorful Seaming, Waterproof Cloth"
        )

        printful_name = (
            "Gaming Mouse Pad "
            '(White / 18"x16")'
        )

        result = service.are_products_comparable(
            first_name=cj_name,
            second_name=printful_name,
        )

        self.assertTrue(
            result
        )

    def test_does_not_match_mouse_with_mouse_pad(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name="Gaming Wireless Mouse",
            second_name="Gaming Mouse Pad",
        )

        self.assertFalse(
            result
        )

    def test_matches_desk_mat_with_mouse_pad_family(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name="Large Gaming Desk Mat",
            second_name="Gaming Mouse Pad",
        )

        self.assertTrue(
            result
        )

    def test_does_not_match_same_family_with_very_different_dimensions(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name="Gaming Mouse Mat",
            second_name="Gaming Mouse Pad",
            first_dimensions=(300, 800),
            second_dimensions=(457, 406),
        )

        self.assertFalse(
            result
        )

    def test_matches_same_family_with_similar_dimensions(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name="Gaming Mouse Mat",
            second_name="Gaming Mouse Pad",
            first_dimensions=(450, 400),
            second_dimensions=(457, 406),
        )

        self.assertTrue(
            result
        )

    def test_matches_similar_dimensions_when_orientation_is_reversed(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name="Gaming Mouse Mat",
            second_name="Gaming Mouse Pad",
            first_dimensions=(400, 450),
            second_dimensions=(457, 406),
        )

        self.assertTrue(
            result
        )

    def test_matches_exact_same_dimensions_when_width_and_length_are_swapped(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name="Gaming Mouse Mat",
            second_name="Gaming Mouse Pad",
            first_dimensions=(350, 500),
            second_dimensions=(500, 350),
        )

        self.assertTrue(
            result
        )

    def test_returns_false_when_dimensions_are_invalid(
        self,
    ):
        service = SupplierProductMatchingService()

        result = service.are_products_comparable(
            first_name="Gaming Mouse Mat",
            second_name="Gaming Mouse Pad",
            first_dimensions=(0, 500),
            second_dimensions=(500, 350),
        )

        self.assertFalse(result)

    def test_returns_false_when_dimensions_have_invalid_shape(
        self,
    ):
        service = SupplierProductMatchingService()

        result = service.are_products_comparable(
            first_name="Gaming Mouse Mat",
            second_name="Gaming Mouse Pad",
            first_dimensions=(500,),
            second_dimensions=(500, 350),
        )

        self.assertFalse(result)

    def test_matches_similar_ceramic_mug_names(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Ceramic Coffee Cup Ceramic Mug"
            ),
            second_name=(
                "White Glossy Mug 11 oz"
            ),
        )

        self.assertTrue(
            result
        )

    def test_matches_similar_cotton_tote_bag_names(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Women's Canvas Large Capacity "
                "Versatile Tote Bag"
            ),
            second_name=(
                "Cotton Canvas Tote Bag 15 x 16 in"
            ),
        )

        self.assertTrue(
            result
        )

    def test_does_not_match_canvas_bag_strap_with_tote_bag(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Extension Strap Wash Canvas Bag "
                "Strap Accessories"
            ),
            second_name=(
                "Cotton Canvas Tote Bag"
            ),
        )

        self.assertFalse(
            result
        )

    def test_does_not_match_mugs_with_very_different_capacities(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Ceramic Coffee Mug 200ml"
            ),
            second_name=(
                "White Ceramic Mug 11 oz"
            ),
            first_capacity_ml=200,
            second_capacity_ml=325,
        )

        self.assertFalse(
            result
        )

    def test_matches_mugs_with_similar_capacities(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Ceramic Coffee Mug 11 oz"
            ),
            second_name=(
                "White Ceramic Mug 330ml"
            ),
            first_capacity_ml=325,
            second_capacity_ml=330,
        )

        self.assertTrue(
            result
        )

    def test_rejects_offer_without_dimensions_when_target_has_dimensions(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Tote Bag Shoulder Strap"
            ),
            second_name=(
                "Cotton Canvas Tote Bag "
                "15 x 16 in"
            ),
            first_dimensions=None,
            second_dimensions=(
                381,
                406,
            ),
        )

        self.assertFalse(
            result
        )

    def test_rejects_offer_without_capacity_when_target_has_capacity(
        self,
    ):
        service = (
            SupplierProductMatchingService()
        )

        result = service.are_products_comparable(
            first_name=(
                "Ceramic Coffee Mug"
            ),
            second_name=(
                "White Ceramic Mug 11 oz"
            ),
            first_capacity_ml=None,
            second_capacity_ml=325,
        )

        self.assertFalse(
            result
        )