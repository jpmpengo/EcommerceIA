from product_intelligence.models import ProductOpportunity


class RestockOpportunityService:

    @staticmethod
    def find_product(offer):
        opportunity = (
            ProductOpportunity.objects
            .filter(
                status="published",
                published_product__isnull=False,
                published_product__stock=0,
                supplier_offer__supplier=offer.supplier,
                supplier_offer__supplier_product_id=(
                    offer.supplier_product_id
                ),
            )
            .select_related(
                "published_product",
            )
            .order_by(
                "-detected_at",
            )
            .first()
        )

        if opportunity is None:
            return None

        return opportunity.published_product
        