from typing import Literal
from pydantic import BaseModel, Field


class SaturationCompetitorEvidence(BaseModel):
    offer_url: str
    seller_name: str
    country: Literal["FR", "BE", "ES"]


class OpportunitySaturationSearchResponse(BaseModel):
    level: Literal["very_low", "low", "moderate", "high", "very_high", "indeterminate"]
    justification: str
    sources: list[str] = Field(default_factory=list)
    sellers: list[str] = Field(default_factory=list)
    competitor_evidence: list[SaturationCompetitorEvidence] = Field(default_factory=list)


def is_candidate_product_url(url):
    from urllib.parse import urlparse, parse_qs
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    host = parsed.hostname.lower().removeprefix("www.")
    if host in ("example.com", "example.org", "example.net") or host.endswith((".example.com", ".example.org", ".example.net")):
        return False
    path = parsed.path.strip("/").lower()
    if host.endswith("amazon.fr") and path == "s":
        return False
    if not path:
        return parsed.hostname.lower() == "avlo-deerlijk.be" and bool(parse_qs(parsed.query).get("product"))
    segments = path.split("/")
    return not any(segment in ("faq", "search", "collections", "category", "categories") or segment.startswith("faq-") for segment in segments)


class OpportunitySaturationSearchService:
    INSTRUCTIONS = """Etudie la saturation concurrentielle pour le produit fourni sur les marches FR, BE et ES. Recherche des offres publiques de produits reellement equivalents. Distingue les vendeurs et evite les doublons. Evalue la presence concurrentielle sans utiliser les prix comparables ni leur dispersion. Justifie ton niveau de saturation par des observations verifiables et des URL publiques. Ne confonds pas le nombre de resultats de recherche avec le nombre total de concurrents. Ne fabrique aucune preuve. Chaque preuve doit pointer vers une fiche produit individuelle, jamais vers une page de categorie, une page de recherche ou un accueil. Renseigne uniquement des vendeurs explicitement identifies sur les offres, sans noms generiques ou supposes. La liste sellers doit contenir exactement les noms distincts presents dans competitor_evidence, sans ajout ni omission. Un meme vendeur present dans plusieurs pays reste un seul concurrent. Ne conserve pas plusieurs vendeurs associes a une meme URL sans preuve individuelle distincte. Si les informations sont insuffisantes, retourne indeterminate."""

    def __init__(self, client):
        self.client = client

    def search(self, product_name, product_attributes):
        result = self.client.generate(instructions=self.INSTRUCTIONS, context={"target_countries": ["FR", "BE", "ES"], "product": {"name": product_name, "attributes": product_attributes}}, response_model=OpportunitySaturationSearchResponse, use_web_search=True)
        from urllib.parse import urlparse, parse_qs
        result = dict(result)
        original_urls = [u for u in (result.get("sources") or [])] + [e.get("offer_url") for e in (result.get("competitor_evidence") or []) if isinstance(e, dict)]
        result["original_url_count"] = len(original_urls)
        result["invalid_url_count"] = sum(not is_candidate_product_url(u) for u in original_urls)
        result["all_urls_invalid"] = bool(original_urls) and result["invalid_url_count"] == len(original_urls)
        result["sources"] = [u for u in (result.get("sources") or []) if is_candidate_product_url(u)]
        result["competitor_evidence"] = [e for e in (result.get("competitor_evidence") or []) if not isinstance(e, dict) or is_candidate_product_url(e.get("offer_url"))]
        sources = result.get("sources") or []
        valid_sources = [url for url in sources if is_candidate_product_url(url)]
        evidence_urls = [evidence.get("offer_url") for evidence in (result.get("competitor_evidence") or []) if isinstance(evidence, dict)]
        declared_sellers = {name.strip().casefold() for name in (result.get("sellers") or []) if isinstance(name, str) and name.strip()}
        evidenced_sellers = {evidence.get("seller_name").strip().casefold() for evidence in (result.get("competitor_evidence") or []) if isinstance(evidence, dict) and isinstance(evidence.get("seller_name"), str) and evidence.get("seller_name").strip()}
        invalid_evidence_countries = any(not isinstance(evidence, dict) or evidence.get("country") not in ("FR", "BE", "ES") for evidence in (result.get("competitor_evidence") or []))
        invalid_evidence_sellers = any(not isinstance(evidence, dict) or not isinstance(evidence.get("seller_name"), str) or not evidence.get("seller_name").strip() for evidence in (result.get("competitor_evidence") or []))
        original_level = result.get("level")
        if invalid_evidence_sellers or invalid_evidence_countries or not valid_sources or not str(result.get("justification") or "").strip() or (result.get("level") in ("high", "very_high") and (not evidence_urls or len(set(evidence_urls)) < 2 or any(not isinstance(url, str) or urlparse(url).netloc.lower().removeprefix("www.") + urlparse(url).path.rstrip("/") + ("?" + urlparse(url).query if urlparse(url).query else "") not in {urlparse(source).netloc.lower().removeprefix("www.") + urlparse(source).path.rstrip("/") + ("?" + urlparse(source).query if urlparse(source).query else "") for source in valid_sources} for url in evidence_urls) or False)) or (result.get("level") in ("high", "very_high") and (not result.get("competitor_evidence") or len({name.strip().casefold() for evidence in (result.get("competitor_evidence") or []) if isinstance(evidence, dict) for name in [evidence.get("seller_name")] if isinstance(name, str) and name.strip()}) < 2)):
            return {**result, "original_level": original_level, "level": "indeterminate", "validation_reason": "Preuves concurrentielles insuffisantes ou non conformes"}
        if result.get("competitor_evidence") and not invalid_evidence_sellers and not invalid_evidence_countries:
            result["sellers"] = list(dict.fromkeys(evidence["seller_name"].strip() for evidence in result["competitor_evidence"] if isinstance(evidence, dict)))
        return {**result, "original_level": original_level, "validation_reason": None}
