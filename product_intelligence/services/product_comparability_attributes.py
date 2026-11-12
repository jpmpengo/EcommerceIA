import re

from product_intelligence.services.variant_features import (
    VariantFeaturesService,
)


class ProductComparabilityAttributesService:

    PACK_PATTERNS = (
        r"\bset\s+of\s+(\d+)\b",
        r"\bpack\s+of\s+(\d+)\b",
        r"\blot\s+(\d+)\b",
        r"\blot de\s+(\d+)\b",
        r"\bpaquet de\s+(\d+)\b",
        r"\b(\d+)\s*pcs?\b",
        r"\b(\d+)\s*pieces?\b",
        r"\b(\d+)\s*unites?\b",
        r"\b(\d+)\s*unidades?\b",
        r"\b(\d+)\s+bands?\b",
        r"\b(\d+)\s+bandes?\b",
        r"\b(\d+)\s+bandas?\b",
        r"\s*(\d+)\s+(?:[A-Za-z-]+\s+){0,4}culottes?\b",
        r"\s*(\d+)\s+(?:[A-Za-z-]+\s+){0,4}briefs?\b",
        r"\s*(\d+)\s+(?:[A-Za-z-]+\s+){0,4}pants?\b",
    )

    def __init__(self, variant_features_service=None):
        self.variant_features_service = (
            variant_features_service
            or VariantFeaturesService()
        )

    def extract(self, name, evidence="", persisted_features=None):
        text = " ".join(
            value for value in (name, evidence) if value
        )
        extracted = self.variant_features_service.extract({"name": text})
        persisted = persisted_features or {}

        return {
            "pack_quantity": (
                persisted.get("pack_quantity")
                or self._extract_pack_quantity(text)
            ),
            "dimensions_mm": (
                persisted.get("dimensions_mm")
                or extracted.get("dimensions_mm")
            ),
            "capacity_ml": (
                persisted.get("capacity_ml")
                or extracted.get("capacity_ml")
            ),
            "size": (
                persisted.get("size")
                or extracted.get("size")
            ),
            "product_family": self._extract_product_family(text),
            "includes_pot": self._extract_includes_pot(text),
        }


    @classmethod
    def _extract_product_family(cls, text):
        value = str(text or "").lower()
        if "macrame" in value and any(term in value for term in ("pot holder", "plant hanger", "porte-pot", "porte plante", "suspension")):
            return "macrame_hanger"
        return None

    @classmethod
    def _extract_includes_pot(cls, text):
        value = str(text or "").lower()
        excluded = (
            "pot not included",
            "plant and pot in picture not included",
            "pot et la plante ne sont pas inclus",
            "pot non inclus",
            "plante et pot non inclus",
        )
        if any(term in value for term in excluded):
            return False
        return None

    @classmethod
    def _extract_pack_quantity(cls, text):
        normalized = str(text or "").strip()

        for pattern in cls.PACK_PATTERNS:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match and int(match.group(1)) > 0:
                return int(match.group(1))

        return None
