import ssl
import io

from PIL import Image, UnidentifiedImageError
import httpx
import truststore


class VisualImageAccessibilityService:
    @staticmethod
    def is_accessible(url):
        if not isinstance(url, str) or not url.startswith("https://"):
            return False
        try:
            context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            with httpx.Client(verify=context, timeout=15.0, follow_redirects=True) as client:
                response = client.get(url)
                if response.status_code != 200:
                    return False
                with Image.open(io.BytesIO(response.content)) as image:
                    image.verify()
                    return image.format in {"JPEG", "PNG", "GIF", "WEBP"}
        except (httpx.HTTPError, OSError, ValueError, UnidentifiedImageError):
            return False

    @staticmethod
    def fetch_image_data_url(url):
        import base64
        import httpcore
        from urllib.parse import urlsplit
        from product_intelligence.services.safe_network_backend import SafeNetworkBackend
        if not isinstance(url, str):
            return None
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
            return None
        try:
            context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            transport = httpx.HTTPTransport(verify=context, trust_env=False)
            transport._pool.close()
            transport._pool = httpcore.ConnectionPool(ssl_context=context, network_backend=SafeNetworkBackend())
            with httpx.Client(transport=transport, timeout=15.0, follow_redirects=False, trust_env=False) as client:
                with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        return None
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 5 * 1024 * 1024:
                            return None
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
                image_format = image.format
            mime = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif", "WEBP": "image/webp"}.get(image_format)
            if not mime:
                return None
            return "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
        except (httpx.HTTPError, OSError, ValueError, UnidentifiedImageError, OverflowError):
            return None
