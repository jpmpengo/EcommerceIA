import re
import unicodedata


class SupplierCategoryMatchingService:

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
        "small",
        "space",
        "spaces",
        "saving",
    }

    @classmethod
    def _tokens(
        cls,
        value,
    ):
        ascii_value = unicodedata.normalize(
            "NFKD",
            (value or "").lower(),
        ).encode("ascii", "ignore").decode("ascii")

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            ascii_value,
        )

        return {
            token
            for token in normalized.split()
            if (
                len(token) >= 3
                and token
                not in cls.IGNORED_WORDS
            )
        }

    @staticmethod
    def _token_matches(product_token, keyword_token):
        if product_token == keyword_token:
            return True

        shorter = min(len(product_token), len(keyword_token))
        if shorter < 5:
            return False

        return (
            product_token.startswith(keyword_token)
            or keyword_token.startswith(product_token)
        )

    def is_relevant(
        self,
        product_name,
        search_keyword,
        alternative_keywords=None,
    ):
        for alternative_keyword in (alternative_keywords or []):
            if self.is_relevant(
                product_name=product_name,
                search_keyword=alternative_keyword,
            ):
                return True

        product_tokens = self._tokens(
            product_name
        )

        keyword_tokens = self._tokens(
            search_keyword
        )

        if (
            not product_tokens
            or not keyword_tokens
        ):
            return False

        for anchor_group in self.ANCHOR_GROUPS:
            if keyword_tokens & anchor_group:
                if not product_tokens & anchor_group:
                    return False

        if "treadmill" in keyword_tokens:
            return "treadmill" in product_tokens or ("walking" in product_tokens and bool(product_tokens & {"pad", "machine"}))

        matched_keyword_tokens = {
            keyword_token
            for keyword_token in keyword_tokens
            if any(
                self._token_matches(
                    product_token,
                    keyword_token,
                )
                for product_token in product_tokens
            )
        }

        minimum_matches = min(
            3,
            len(keyword_tokens),
        )

        return (
            len(matched_keyword_tokens)
            >= minimum_matches
        )
