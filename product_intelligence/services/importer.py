from decimal import Decimal

from product_intelligence.models import ProductOpportunity


class OpportunityImporter:
    @staticmethod
    def import_from_provider(provider):
        created_count = 0
        skipped_count = 0

        products = provider.get_products()

        for product_data in products:
            name = product_data["name"]
            source_name = provider.__class__.__name__

            opportunity, created = (
                ProductOpportunity.objects.get_or_create(
                    name=name,
                    source_name=source_name,
                    defaults={
                        "description": product_data.get(
                            "description",
                            "",
                        ),
                        "supplier_price": Decimal(
                            str(product_data["supplier_price"])
                        ),
                        "market_price": Decimal(
                            str(product_data["market_price"])
                        ),
                        "shipping_cost": Decimal(
                            str(
                                product_data.get(
                                    "shipping_cost",
                                    0,
                                )
                            )
                        ),
                        "other_costs": Decimal(
                            str(
                                product_data.get(
                                    "other_costs",
                                    0,
                                )
                            )
                        ),
                        "demand_score": product_data.get(
                            "demand_score",
                            0,
                        ),
                        "competition_score": product_data.get(
                            "competition_score",
                            0,
                        ),
                        "initial_stock": product_data.get(
                            "initial_stock",
                            0,
                        ),
                        "status": "detected",
                    },
                )
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

        return {
            "created": created_count,
            "skipped": skipped_count,
        }
        