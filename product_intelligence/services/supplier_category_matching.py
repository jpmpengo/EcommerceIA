import re


class SupplierCategoryMatchingService:

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
        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            (value or "").lower(),
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

    def is_relevant(
        self,
        product_name,
        search_keyword,
    ):
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

        common_tokens = (
            product_tokens
            & keyword_tokens
        )

        minimum_matches = min(
            2,
            len(keyword_tokens),
        )

        return (
            len(common_tokens)
            >= minimum_matches
        )