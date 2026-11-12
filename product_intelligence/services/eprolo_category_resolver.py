import re
import unicodedata


class EproloCategoryResolver:
    """Maps only explicitly supported product families.

    Returning None is intentional: EPROLO must not fall back to an
    unfiltered global-catalog scan when a category is uncertain.
    """

    RULES = (
        (
            ("garden", "gardening", "planter", "flower pot"),
            (15, 134),
        ),
        (
            ("cycling", "bicycle", "bike", "velo"),
            (26, 67),
        ),
        (
            (
                "computer office",
                "laptop",
                "desk organizer",
                "workspace",
                "office desk",
                "bureau",
            ),
            (13, 126),
        ),
    )

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize(
            "NFKD", str(value or "")
        ).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"[^a-z0-9]+", " ", value.lower())
        return " ".join(value.split())

    def resolve(self, *values):
        haystack = self._normalize(" ".join(
            str(value or "") for value in values
        ))
        for terms, category in self.RULES:
            if any(term in haystack for term in terms):
                return {
                    "ware_type_id": category[0],
                    "ware_type_two_id": category[1],
                }
        return None
