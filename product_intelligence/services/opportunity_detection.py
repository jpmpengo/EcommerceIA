
from product_intelligence.models import (
    ProductOpportunity,
    SupplierOffer,
)


class OpportunityDetectionService:

    def __init__(
        self,
        ebay_cj_bridge_service,
        etsy_cj_bridge_service=None,
        woocommerce_cj_bridge_service=None,
    ):
        self.ebay_cj_bridge_service = ebay_cj_bridge_service
        self.etsy_cj_bridge_service = etsy_cj_bridge_service
        self.woocommerce_cj_bridge_service = (
            woocommerce_cj_bridge_service
        )

    def _get_bridge_for_source(
        self,
        source,
    ):
        if source == "ebay":
            return self.ebay_cj_bridge_service

        if source == "etsy":
            if self.etsy_cj_bridge_service is None:
                raise ValueError(
                    "Etsy CJ bridge service is required."
                )

            return self.etsy_cj_bridge_service

        if source == "woocommerce":
            if self.woocommerce_cj_bridge_service is None:
                raise ValueError(
                    "WooCommerce CJ bridge service is required."
                )

            return self.woocommerce_cj_bridge_service

        raise ValueError(
            "Unsupported market observation source."
        )

    def process_observation(
        self,
        market_observation,
        supplier,
    ):
        if market_observation.observed_price is None:
            raise ValueError(
                "Market observation must have an observed price."
            )

        already_processed = SupplierOffer.objects.filter(
            supplier=supplier,
            market_observation=market_observation,
        ).exists()

        if (
            already_processed
            and not self._can_reprocess_for_restock(
                market_observation=market_observation,
                supplier=supplier,
            )
        ):
            return None

        bridge = self._get_bridge_for_source(
            market_observation.source,
        )

        try:
            return bridge.search_and_create_opportunity(
                market_observation=market_observation,
                supplier=supplier,
            )

        except ValueError as exc:
            if str(exc) == "No reliable CJ product match found.":
                return None

            raise

    def process_observations(
        self,
        market_observations,
        supplier,
    ):
        results = []

        for market_observation in market_observations:
            try:
                result = self.process_observation(
                    market_observation=market_observation,
                    supplier=supplier,
                )
            except ValueError as exc:
                if str(exc) == (
                    "Market observation must have an observed price."
                ):
                    continue

                raise

            if result is not None:
                results.append(result)

        return results

    def process_observations_with_summary(
        self,
        market_observations,
        supplier,
    ):
        summary = {
            "processed": 0,
            "created": 0,
            "skipped_no_price": 0,
            "skipped_no_match": 0,
            "skipped_already_processed": 0,
            "results": [],
        }

        for market_observation in market_observations:
            summary["processed"] += 1

            if market_observation.observed_price is None:
                summary["skipped_no_price"] += 1
                continue

            already_processed = SupplierOffer.objects.filter(
                supplier=supplier,
                market_observation=market_observation,
            ).exists()

            if (
                already_processed
                and not self._can_reprocess_for_restock(
                    market_observation=market_observation,
                    supplier=supplier,
                )
            ):
                summary["skipped_already_processed"] += 1
                continue

            result = self.process_observation(
                market_observation=market_observation,
                supplier=supplier,
            )

            if result is None:
                summary["skipped_no_match"] += 1
                continue

            summary["created"] += 1
            summary["results"].append(result)

        return summary
    
    def _can_reprocess_for_restock(
        self,
        market_observation,
        supplier,
    ):
        old_opportunity = (
            ProductOpportunity.objects
            .filter(
                supplier_offer__supplier=supplier,
                supplier_offer__market_observation=market_observation,
                status="published",
                published_product__isnull=False,
                published_product__stock=0,
            )
            .order_by(
                "-detected_at",
            )
            .first()
        )

        return old_opportunity is not None
        