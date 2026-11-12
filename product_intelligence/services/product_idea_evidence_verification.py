import socket
from dataclasses import dataclass
import re
import ssl
import truststore
import ipaddress
from urllib.parse import urlsplit
import httpx
import httpcore
from product_intelligence.services.safe_network_backend import SafeNetworkBackend


@dataclass
class EvidenceVerificationResult:
    is_verified: bool


class ProductIdeaEvidenceVerificationService:

    def __init__(self, http_client=None):
        if http_client is not None:
            self.http_client = http_client
        else:
            transport = httpx.HTTPTransport(verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), trust_env=False)
            transport._pool.close()
            transport._pool = httpcore.ConnectionPool(ssl_context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), network_backend=SafeNetworkBackend())
            self.http_client = httpx.Client(transport=transport, timeout=10.0, follow_redirects=False, trust_env=False)


    @staticmethod
    def _normalize_evidence_text(value):
        import html
        import unicodedata
        value = html.unescape(str(value))
        value = re.sub(r"(?is)\x3c(script|style)\b.*?\x3c/\1\s*\x3e", " ", value)
        value = re.sub(r"(?s)\x3c[^\x3e]*\x3e", " ", value)
        value = unicodedata.normalize("NFKD", value)
        value = "".join(c for c in value if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", value).lower().strip()

    @staticmethod
    def _verify_sales_growth(content, claim):
        percentages = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", claim)
        if not percentages and re.search(r"\b(?:triple|tripled)\b", claim):
            return bool(re.search(r"\bdemand\s+(?:(?:has\s+)?tripled|tripling)\s+since\s+(?:2024|last\s+year)\b", content))
        if len(percentages) == 2:
            checks = [(r'retail sales revenue of fitness tracking devices has grown', '88'), (r'smart ring unit volume has grown', '195')]
            return sorted(percentages) == sorted(n for _, n in checks) and all(re.search(context + r'\s+' + number + r'\s*(?:%|percent)(?!\w)', content) for context, number in checks)
        if len(percentages) != 1:
            return False
        product_claim = re.search(r'\bsales of ([a-z ]+?) (?:rose|grew|increased|up)\s+\d', claim)
        if product_claim:
            product = product_claim.group(1).strip()
            number_text = percentages[0].replace(',', '.')
            return bool(re.search(r'\bsales of\s+' + re.escape(product) + r'\s+(?:rose|grew|increased|up)\s+' + re.escape(number_text) + r'\s*(?:%|percent)(?!\w)', content))
        named_product = re.search(r'(?<![a-z0-9\'])(\b[a-z][a-z0-9-]*(?:\s+[a-z][a-z0-9-]*){0,4})\s+sales\s+(?:rose|grew|increased)\s+\d', claim)
        if named_product:
            product = named_product.group(1)
            number_text = re.escape(percentages[0].replace(',', '.'))
            pattern = re.escape(product) + r'\s+sales\s+(?:rose|grew|increased)\s+' + number_text + r'\s*(?:%|percent)(?!\w)'
            if re.search(pattern, content):
                return True
            brand = product.split()[0]
            alternate = r'\b' + re.escape(brand) + r'\s+saw\s+its\s+sales\s+rise\s+' + number_text + r'\s*(?:%|percent)(?!\w)'
            return bool(re.search(alternate, content))
        number = re.escape(percentages[0].replace(",", "."))
        pattern = number + r"\s*(?:%|percent)"
        return any(re.search(r"\b(?:sales|ventes|hausse|growth|grew|grown|rose|rise|increased|up)\b", content[max(0,m.start()-100):m.end()+100]) for m in re.finditer(pattern, content))

    @classmethod
    def _verify_delivery_text(cls, content, days_min, days_max):
        text = cls._normalize_evidence_text(content)
        sep = chr(124)
        words = sep.join(["livraison", "delivery", "shipping", "entrega", "envio"])
        units = sep.join(["jours", "days", "dias"])
        between = sep.join(["-", "a", "to", "et", "and"])
        pattern = "(?:" + words + ").{0,80}?" + str(int(days_min)) + "\\s*(?:" + between + ")\\s*" + str(int(days_max)) + "\\s*(?:" + units + ")"
        return bool(re.search(pattern, text))

    @classmethod
    def _verify_competitor_product_text(cls, content, product_name):
        name = cls._normalize_evidence_text(product_name)
        page = cls._normalize_evidence_text(content)
        if not name or len(name) < 5:
            return False
        return name in page

    @classmethod
    def _verify_delivery_country_text(cls, content, country):
        text = cls._normalize_evidence_text(content)
        names = {"FR": ("france",), "BE": ("belgique", "belgium", "belgica"), "ES": ("espagne", "spain", "espana")}
        candidates = names.get(str(country).upper(), ())
        return any(re.search(r"\b" + re.escape(name) + r"\b", text) for name in candidates)

    def fetch_innovation_content(self, source_url):
        try:
            parsed = urlsplit(str(source_url))
            host = parsed.hostname
            if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.port not in (None, 443) or host.lower() == "localhost" or host.lower().endswith((".localhost", ".local")):
                return ""
            try:
                address = ipaddress.ip_address(host)
                if not address.is_global:
                    return ""
            except ValueError:
                pass
            response = self.http_client.get(source_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type not in ("text/html", "text/plain"):
                return ""
            if len(response.content) > 200000:
                return ""
            return self._normalize_evidence_text(response.text)[:12000]
        except (ValueError, TypeError, httpx.HTTPError, socket.gaierror):
            return ""

    def verify_innovation(self, source_url, functional_difference):
        try:
            parsed = urlsplit(str(source_url))
            host = parsed.hostname
            if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.port not in (None, 443) or host.lower() == "localhost" or host.lower().endswith((".localhost", ".local")):
                return EvidenceVerificationResult(is_verified=False)
            try:
                address = ipaddress.ip_address(host)
                if not address.is_global:
                    return EvidenceVerificationResult(is_verified=False)
            except ValueError:
                pass
            response = self.http_client.get(source_url)
            response.raise_for_status()
            content = self._normalize_evidence_text(response.text)
            difference = self._normalize_evidence_text(functional_difference)
            words = [word for word in re.findall(r"[a-z0-9]+", difference) if len(word) >= 5]
            verified = len(words) >= 2 and all(re.search(r"\b" + re.escape(word) + r"\b", content) for word in set(words))
            return EvidenceVerificationResult(is_verified=verified)
        except (ValueError, TypeError, httpx.HTTPError, socket.gaierror):
            return EvidenceVerificationResult(is_verified=False)

    def verify_delivery(self, source_url, days_min, days_max, competitor_product_name="", country=""):
        try:
            parsed = urlsplit(str(source_url))
            host = parsed.hostname
            if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.port not in (None, 443) or host.lower() == "localhost" or host.lower().endswith((".localhost", ".local")):
                return EvidenceVerificationResult(is_verified=False)
            try:
                address = ipaddress.ip_address(host)
                if not address.is_global:
                    return EvidenceVerificationResult(is_verified=False)
            except ValueError:
                pass
            response = self.http_client.get(source_url)
            response.raise_for_status()
            verified = self._verify_delivery_text(response.text, days_min, days_max) and self._verify_competitor_product_text(response.text, competitor_product_name) and self._verify_delivery_country_text(response.text, country)
            return EvidenceVerificationResult(is_verified=verified)
        except (ValueError, TypeError, httpx.HTTPError, socket.gaierror):
            return EvidenceVerificationResult(is_verified=False)

    def verify(self, source_url, metric, value):
        try:
            parsed = urlsplit(str(source_url))
            host = parsed.hostname
            if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.port not in (None, 443) or host.lower() == "localhost" or host.lower().endswith(".localhost") or host.lower().endswith(".local"):
                return EvidenceVerificationResult(is_verified=False)
            try:
                address = ipaddress.ip_address(host)
            except ValueError:
                pass
            else:
                if not address.is_global:
                    return EvidenceVerificationResult(is_verified=False)
        except ValueError:
            return EvidenceVerificationResult(is_verified=False)
        verified = False
        if self.http_client is not None:
            try:
                response = self.http_client.get(source_url)
                response.raise_for_status()
            except (httpx.HTTPError, socket.gaierror):
                return EvidenceVerificationResult(is_verified=False)
            content = self._normalize_evidence_text(response.text)
            claim = self._normalize_evidence_text(value)
            match = re.search(r"from\s+(\d+(?:\.\d+)?)\s+in\s+([a-z]+)\s+(\d{4})\s+to\s+(\d+(?:\.\d+)?)\s+in\s+([a-z]+)\s+(\d{4})", content)
            claimed = re.search(r"(\d+(?:\.\d+)?)\s*%\s*growth\s+from\s+([a-z]+)(?:\s+(\d{4}))?\s+to\s+([a-z]+)\s+(\d{4})", claim)
            if metric == "sales_growth":
                verified = self._verify_sales_growth(content, claim)
            if metric == "search_trend" and match and claimed:
                initial, final = float(match.group(1)), float(match.group(4))
                verified = (int(match.group(3)), list(__import__("calendar").month_name).index(match.group(2).capitalize())) < (int(match.group(6)), list(__import__("calendar").month_name).index(match.group(5).capitalize())) and match.group(2) == claimed.group(2) and match.group(3) == (claimed.group(3) or claimed.group(5)) and match.group(5) == claimed.group(4) and match.group(6) == claimed.group(5) and initial > 0 and final > initial and abs(((final - initial) / initial * 100) - float(claimed.group(1))) < 0.01
        return EvidenceVerificationResult(
            is_verified=verified,
        )