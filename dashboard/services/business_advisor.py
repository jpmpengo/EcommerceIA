"""
BusinessAdvisor

Responsabilité
--------------
Prioriser les recommandations à présenter au commerçant.

Ce service :
- collecte une vue synthétique de l'activité ;
- sélectionne les opportunités prioritaires ;
- prépare les données du briefing ;
- classe les recommandations.

Ce service ne :
- ne crée jamais de produit ;
- n'exécute jamais les décisions du commerçant.

Utilisé par
-----------
- DailyAssistant
- Centre de recommandations

Dépend de
---------
- Product
- Order
- ProductOpportunity
- OpportunityAdvisor
"""

from orders.models import Order
from products.models import Product
from product_intelligence.models import ProductOpportunity
from product_intelligence.services.advisor import OpportunityAdvisor

from django.db.models import Q
from django.utils import timezone


class BusinessAdvisor:
    def get_business_brief(self):
        product_count = Product.objects.count()

        active_product_count = Product.objects.filter(
            is_available=True,
        ).count()

        order_count = Order.objects.count()

        unpaid_order_count = Order.objects.filter(
            paid=False,
        ).count()

        opportunity_count = ProductOpportunity.objects.count()

        detected_opportunity_count = ProductOpportunity.objects.filter(
            status__in=["detected", "review"],
        ).count()

        approved_opportunities = ProductOpportunity.objects.filter(
            status="approved",
            published_product__isnull=True,
        ).filter(
            Q(postponed_until__isnull=True)
            | Q(postponed_until__lte=timezone.now())
        )

        approved_opportunity_count = approved_opportunities.count()

        low_stock_count = Product.objects.filter(
            is_available=True,
            stock__lte=2,
        ).count()

        ranked_opportunities = (
            OpportunityAdvisor.rank_opportunities(
                approved_opportunities
            )
        )

        top_opportunities = []

        for opportunity in ranked_opportunities:
            recommendation = OpportunityAdvisor.get_recommendation(
                opportunity
            )

            ai_recommendation = getattr(opportunity, "ai_recommendation", None)
            ai_decision_messages = {
                "recommend": ("Emma recommande de presenter cette opportunite au commercant.", "success"),
                "study": ("Emma demande des complements d etude avant decision.", "warning"),
                "reject": ("Emma deconseille cette opportunite.", "danger"),
            }
            ai_decision = getattr(ai_recommendation, "decision", None)
            recommendation["decision"], recommendation["level"] = ai_decision_messages.get(
                ai_decision, ("Recommandation IA non disponible.", "warning")
            )

            top_opportunities.append(
                {
                    "opportunity": opportunity,
                    "priority": (
                        OpportunityAdvisor.calculate_priority(
                            opportunity
                        )
                    ),
                    "recommendation": recommendation,
                }
            )

        return {
            "statistics": {
                "product_count": product_count,
                "active_product_count": active_product_count,
                "order_count": order_count,
                "opportunity_count": opportunity_count,
            },
            "opportunities": {
                "detected_count": detected_opportunity_count,
                "approved_count": approved_opportunity_count,
            },
            "orders": {
                "unpaid_count": unpaid_order_count,
            },
            "stock": {
                "low_count": low_stock_count,
            },
            "top_opportunities": top_opportunities,
            "main_mission": None,
            "alerts": [],
        }
        