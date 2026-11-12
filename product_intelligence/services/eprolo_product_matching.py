import re
import unicodedata


class EproloProductMatchingService:
    MINIMUM_COMMON_TERMS = 2

    ANCHOR_GROUPS = (
        {"bike", "bicycle", "cycling", "cyclist"},
    )

    IGNORED_WORDS = {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "on",
        "the",
        "to",
        "with",
    }

    @classmethod
    def _tokens(cls, value):
        normalized = unicodedata.normalize(
            "NFKD", str(value or "")
        ).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            normalized.lower(),
        )
        return {
            token
            for token in normalized.split()
            if (
                len(token) >= 3
                and token not in cls.IGNORED_WORDS
            )
        }

    def is_relevant(self, product_name, search_keyword):
        product_tokens = self._tokens(product_name)
        keyword_tokens = self._tokens(search_keyword)
        if not product_tokens or not keyword_tokens:
            return False

        for anchor_group in self.ANCHOR_GROUPS:
            if keyword_tokens & anchor_group:
                if not product_tokens & anchor_group:
                    return False

        required_matches = min(
            self.MINIMUM_COMMON_TERMS,
            len(keyword_tokens),
        )
        return len(
            product_tokens & keyword_tokens
        ) >= required_matches
