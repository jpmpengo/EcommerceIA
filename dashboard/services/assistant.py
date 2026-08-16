
from .business_advisor import BusinessAdvisor
from django.urls import reverse

class DailyAssistant:
    def get_daily_brief(self):
        advisor = BusinessAdvisor()
        business_brief = advisor.get_business_brief()
        top_opportunities = business_brief["top_opportunities"]

        statistics = business_brief["statistics"]
        opportunities = business_brief["opportunities"]
        orders = business_brief["orders"]
        stock = business_brief["stock"]

        product_count = statistics["product_count"]
        order_count = statistics["order_count"]
        opportunity_count = statistics["opportunity_count"]

        active_product_count = statistics["active_product_count"]

        approved_opportunity_count = opportunities["approved_count"]
        detected_opportunity_count = opportunities["detected_count"]

        unpaid_order_count = orders["unpaid_count"]
        low_stock_count = stock["low_count"]

        missions = []

        if low_stock_count > 0:
            missions.append(
                {
                    "priority": 100,
                    "level": "danger",
                    "icon": "📦",
                    "title": "Stock à surveiller",
                    "message": (
                        f"{low_stock_count} produit(s) "
                        "ont un stock faible."
                    ),
                    "action_label": "Voir les produits",
                    "action_url": "/produits/",
                }
            )

        if approved_opportunity_count > 0:
            missions.append(
                {
                    "priority": 90,
                    "level": "success",
                    "icon": "💡",
                    "title": "Produits prêts à publier",
                    "message": (
                        f"{approved_opportunity_count} "
                        "opportunité(s) approuvée(s) "
                        "peuvent rejoindre le catalogue."
                    ),
                    "action_label": "Examiner les opportunités",
                    "action_url": reverse("recommendations:list"),
                }
            )

        if unpaid_order_count > 0:
            missions.append(
                {
                    "priority": 80,
                    "level": "warning",
                    "icon": "🛒",
                    "title": "Commandes non payées",
                    "message": (
                        f"{unpaid_order_count} commande(s) "
                        "ne sont pas encore payées."
                    ),
                    "action_label": "Voir les commandes",
                    "action_url": "/admin/orders/order/",
                }
            )

        if detected_opportunity_count > 0:
            missions.append(
                {
                    "priority": 70,
                    "level": "info",
                    "icon": "👀",
                    "title": "Opportunités à examiner",
                    "message": (
                        f"{detected_opportunity_count} "
                        "opportunité(s) doivent être analysées."
                    ),
                    "action_label": None,
                    "action_url": None,
                }
            )

        missions.sort(
            key=lambda mission: mission["priority"],
            reverse=True,
        )

        main_mission = missions[0] if missions else None

        if main_mission:
            summary = (
                "Voici la mission qui mérite votre attention "
                "en premier aujourd'hui."
            )
        else:
            summary = (
                "Tout est sous contrôle. "
                "Aucune action urgente aujourd'hui."
            )

        return {
            "greeting": "Bonjour Jean-Paul 👋",
            "summary": summary,
            "main_mission": main_mission,
            "missions": missions[1:] if main_mission else missions,
            "top_opportunities": top_opportunities,
            "product_count": product_count,
            "order_count": order_count,
            "opportunity_count": opportunity_count,
            "active_product_count": active_product_count,
            "approved_opportunity_count": approved_opportunity_count,
            "detected_opportunity_count": detected_opportunity_count,
            "low_stock_count": low_stock_count,
            "unpaid_order_count": unpaid_order_count,
        }



