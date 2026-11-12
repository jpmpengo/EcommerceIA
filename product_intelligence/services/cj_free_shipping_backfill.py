class CJFreeShippingBackfillService:

    def __init__(self, client):
        self.client = client

    def run(self, offers):
        summary = {
            "examined": 0,
            "updated": 0,
            "unchanged": 0,
            "unresolved": 0,
        }
        product_cache = {}

        for offer in offers:
            summary["examined"] += 1
            product_id = getattr(
                offer,
                "supplier_parent_product_id",
                "",
            ) or ""

            if not product_id:
                variant_id = getattr(
                    offer,
                    "supplier_product_id",
                    "",
                ) or ""
                variant = (
                    self.client.get_variant_by_id(
                        variant_id
                    )
                    if variant_id
                    else None
                )
                if (
                    variant_id
                    and not isinstance(variant, dict)
                ):
                    variant = self.client.get_variant_by_id(
                        variant_id
                    )
                if isinstance(variant, dict):
                    product_id = variant.get("pid") or ""

            if not product_id:
                summary["unresolved"] += 1
                continue

            if product_id in product_cache:
                product = product_cache[product_id]
            else:
                product = self.client.get_product_detail(
                    product_id=product_id
                )
                if not isinstance(product, dict):
                    product = self.client.get_product_detail(
                        product_id=product_id
                    )
                if isinstance(product, dict):
                    product_cache[product_id] = product
            if not isinstance(product, dict):
                summary["unresolved"] += 1
                continue

            normalized = self.client.normalize_product(product)
            if "free_shipping" not in normalized:
                summary["unresolved"] += 1
                continue

            value = normalized["free_shipping"]
            if offer.free_shipping is value:
                summary["unchanged"] += 1
                continue

            offer.free_shipping = value
            offer.save(update_fields=["free_shipping"])
            summary["updated"] += 1

        return summary
