from collections import defaultdict

from product_intelligence.models import (
    ProductIdeaVisualReference,
)
from product_intelligence.services.visual_image_accessibility import VisualImageAccessibilityService


class SupplierOfferVisualMatchingService:

    def __init__(self, matching_service, reference_collector=None):
        self.matching_service = matching_service
        self.reference_collector = reference_collector

    def match(self, supplier_offers):
        grouped_offers = defaultdict(list)

        for offer in supplier_offers:
            if not offer.product_idea_id:
                continue
            if not offer.supplier_search_keyword:
                continue
            grouped_offers[
                (
                    offer.product_idea_id,
                    offer.supplier_search_keyword,
                )
            ].append(offer)

        renewed_ideas = set()
        matches = []

        for (product_idea_id, keyword), offers in grouped_offers.items():
            references = [
                {
                    "product_name": reference.product_name,
                    "image_url": reference.image_url,
                }
                for reference in ProductIdeaVisualReference.objects.filter(
                    product_idea_id=product_idea_id,
                    supplier_search_keyword=keyword,
                ).order_by("id")
                if reference.image_url and VisualImageAccessibilityService.is_accessible(reference.image_url)
            ]

            if not references and self.reference_collector is not None and product_idea_id not in renewed_ideas:
                renewed_ideas.add(product_idea_id)
                try:
                    self.reference_collector(offers[0].product_idea)
                except Exception:
                    pass
                references = [{"product_name": ref.product_name, "image_url": ref.image_url} for ref in ProductIdeaVisualReference.objects.filter(product_idea_id=product_idea_id, supplier_search_keyword=keyword).order_by("id") if ref.image_url and VisualImageAccessibilityService.is_accessible(ref.image_url)]

            if not references:
                continue

            result = self.matching_service.match(
                references=references,
                supplier_offers=offers,
                product_idea_name=offers[0].product_idea.name,
            )

            result_matches = result.get("matches", [])

            offers_by_id = {
                offer.id: offer
                for offer in offers
            }

            for match in result_matches:
                offer = offers_by_id.get(
                    match.get("offer_id")
                )
                if offer is None:
                    continue

                offer.visual_match_classification = (
                    match.get("classification") or ""
                )
                offer.visual_score = match.get(
                    "visual_score"
                )
                offer.same_product_probability = (
                    match.get("same_product_probability")
                )
                offer.visual_match_evidence = (
                    match.get("evidence") or ""
                )
                offer.visual_match_differences = (
                    match.get("differences") or []
                )
                offer.save(
                    update_fields=[
                        "visual_match_classification",
                        "visual_score",
                        "same_product_probability",
                        "visual_match_evidence",
                        "visual_match_differences",
                    ]
                )

            matches.extend(result_matches)

        return {"matches": matches}
