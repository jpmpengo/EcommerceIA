import ssl

import httpx
import truststore


class SupplierImageService:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024

    CONTENT_TYPE_EXTENSIONS = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }

    @classmethod
    def download(
        cls,
        image_url,
    ):
        ssl_context = truststore.SSLContext(
            ssl.PROTOCOL_TLS_CLIENT
        )

        response = httpx.get(
            image_url,
            verify=ssl_context,
            timeout=30.0,
        )

        response.raise_for_status()

        content_type = (
            response.headers.get(
                "content-type",
                "",
            )
            .split(";")[0]
            .strip()
            .lower()
        )

        extension = cls.CONTENT_TYPE_EXTENSIONS.get(
            content_type
        )

        if extension is None:
            raise ValueError(
                "Supplier URL did not return a supported image."
            )

        content = response.content

        if len(content) > cls.MAX_IMAGE_SIZE:
            raise ValueError(
                "Supplier image is too large."
            )

        return {
            "content": content,
            "extension": extension,
        }

        