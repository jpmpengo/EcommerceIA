from statistics import median
from urllib.parse import urlsplit


class ComparablePriceSummaryService:

    @classmethod
    def summarize(
        cls,
        supplier_offer,
        currency,
    ):
        comparable_prices = (
            supplier_offer
            .comparable_prices
            .filter(
                qualification_status=(
                    "retained"
                ),
                currency=currency,
            )
            .order_by(
                "observed_price",
                "id",
            )
        )

        prices = [
            comparable_price.observed_price
            for comparable_price
            in comparable_prices
        ]

        source_domains = {
            cls._get_source_domain(
                comparable_price.source_url
            )
            for comparable_price
            in comparable_prices
            if cls._get_source_domain(
                comparable_price.source_url
            )
        }

        if not prices:
            return {
                "currency": currency,
                "retained_count": 0,
                "minimum_price": None,
                "median_price": None,
                "maximum_price": None,
                "source_domain_count": 0,
            }

        return {
            "currency": currency,
            "retained_count": len(prices),
            "minimum_price": min(prices),
            "median_price": median(prices),
            "maximum_price": max(prices),
            "source_domain_count": len(
                source_domains
            ),
        }

    @staticmethod
    def _get_source_domain(
        source_url,
    ):
        hostname = (
            urlsplit(
                source_url
            ).hostname
            or ""
        ).lower()

        if hostname.startswith(
            "www."
        ):
            hostname = hostname[4:]

        return hostname