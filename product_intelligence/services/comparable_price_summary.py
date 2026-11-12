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
                is_current=True,
            )
            .order_by(
                "observed_price",
                "id",
            )
        )

        direct_prices = [c.observed_price for c in comparable_prices if c.commercial_segment == "direct"]
        commercial_median_price = median(direct_prices) if direct_prices else None

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

        collection_batch_id = (
            comparable_prices.first().collection_batch_id
            if prices
            else None
        )

        collection_batch_ids = sorted({str(c.collection_batch_id) for c in comparable_prices if c.collection_batch_id is not None})

        shipping_comparables = [{"source_domain": cls._get_source_domain(c.source_url), "observed_price": str(c.observed_price), "currency": c.currency, "shipping_days_min": c.shipping_days_min, "shipping_days_max": c.shipping_days_max, "shipping_cost": str(c.shipping_cost) if c.shipping_cost is not None else None, "shipping_currency": c.shipping_currency, "free_shipping": c.free_shipping, "shipping_destination_country": c.shipping_destination_country, "shipping_evidence": c.shipping_evidence} for c in comparable_prices]

        if not prices:
            return {
                "currency": currency,
                "collection_batch_id": collection_batch_id,
            "collection_batch_ids": collection_batch_ids,
                "retained_count": 0,
                "minimum_price": None,
                "commercial_median_price": commercial_median_price,
            "median_price": None,
                "maximum_price": None,
                "source_domain_count": 0,
                "shipping_comparables": shipping_comparables,
            }

        return {
            "currency": currency,
            "collection_batch_id": collection_batch_id,
            "collection_batch_ids": collection_batch_ids,
            "retained_count": len(prices),
            "minimum_price": min(prices),
            "commercial_median_price": commercial_median_price,
            "median_price": median(prices),
            "maximum_price": max(prices),
            "source_domain_count": len(
                source_domains
            ),
            "shipping_comparables": shipping_comparables,
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
