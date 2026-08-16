from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from recommendations.services.supplier_image_service import (
    SupplierImageService,
)


class SupplierImageServiceTests(SimpleTestCase):

    @patch(
        "recommendations.services."
        "supplier_image_service.httpx.get"
    )
    def test_download_accepts_jpeg_image(
        self,
        mock_get,
    ):
        response = Mock()
        response.content = b"fake-jpeg-content"
        response.headers = {
            "content-type": "image/jpeg",
        }
        response.raise_for_status.return_value = None

        mock_get.return_value = response

        result = SupplierImageService.download(
            "https://example.com/product.jpg"
        )

        self.assertEqual(
            result["content"],
            b"fake-jpeg-content",
        )

        self.assertEqual(
            result["extension"],
            ".jpg",
        )

    @patch(
    "recommendations.services."
    "supplier_image_service.httpx.get"
    )
    def test_download_rejects_unsupported_content_type(
        self,
        mock_get,
    ):
        response = Mock()
        response.content = b"not-an-image"
        response.headers = {
            "content-type": "text/html",
        }
        response.raise_for_status.return_value = None

        mock_get.return_value = response

        with self.assertRaisesMessage(
            ValueError,
            "Supplier URL did not return a supported image.",
        ):
            SupplierImageService.download(
                "https://example.com/not-image"
            )


    @patch(
        "recommendations.services."
        "supplier_image_service.httpx.get"
    )
    def test_download_rejects_image_that_is_too_large(
        self,
        mock_get,
    ):
        response = Mock()
        response.content = (
            b"x"
            * (
                SupplierImageService.MAX_IMAGE_SIZE
                + 1
            )
        )
        response.headers = {
            "content-type": "image/jpeg",
        }
        response.raise_for_status.return_value = None

        mock_get.return_value = response

        with self.assertRaisesMessage(
            ValueError,
            "Supplier image is too large.",
        ):
            SupplierImageService.download(
                "https://example.com/huge.jpg"
            )