from django.db import transaction
from product_intelligence.models import ComparablePrice
from product_intelligence.services.comparable_price_qualification import ComparablePriceQualificationService


class ComparablePriceStudyIntegrationService:
    MAXIMUM_COMPARABLE_PRICES = 5

    @classmethod
    @transaction.atomic
    def integrate(cls, supplier_offer, collection_batch_id):
        candidates = list(ComparablePrice.objects.select_for_update().filter(supplier_offer=supplier_offer, collection_batch_id=collection_batch_id, is_current=False, qualification_status="retained", commercial_segment="direct").order_by("id"))
        active = list(ComparablePrice.objects.select_for_update().filter(supplier_offer=supplier_offer, is_current=True).order_by("id"))
        normalize = lambda url: ComparablePriceQualificationService._normalize_source_url(url)
        existing_urls = {normalize(item.source_url) for item in active}
        unique_candidates = []
        for item in candidates:
            url = normalize(item.source_url)
            if url not in existing_urls:
                existing_urls.add(url)
                unique_candidates.append(item)
        candidates = unique_candidates
        if not candidates:
            return {"status": "unchanged", "integrated": 0}
        eligible_active = [item for item in active if item.qualification_status == "retained"]
        direct_active = [item for item in eligible_active if item.commercial_segment == "direct"]
        other_active = [item for item in eligible_active if item.commercial_segment != "direct"]
        selected = (direct_active + candidates + other_active)[:cls.MAXIMUM_COMPARABLE_PRICES]
        selected_ids = {item.id for item in selected}
        integrated = len([item for item in candidates if item.id in selected_ids])
        if integrated == 0:
            return {"status": "unchanged", "integrated": 0}
        ComparablePrice.objects.filter(supplier_offer=supplier_offer, is_current=True).exclude(id__in=selected_ids).update(is_current=False)
        ComparablePrice.objects.filter(supplier_offer=supplier_offer, id__in=selected_ids).update(is_current=True)
        return {"status": "integrated", "selected_ids": sorted(selected_ids), "integrated": integrated}
