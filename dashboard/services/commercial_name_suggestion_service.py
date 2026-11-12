class CommercialNameSuggestionService:

    @staticmethod
    def suggest(opportunity):
        name = (opportunity.name or "").strip()

        if not name:
            return None

        normalized = name.lower()

        product_idea = getattr(getattr(opportunity, "supplier_offer", None), "product_idea", None)
        product_idea_name = (getattr(product_idea, "name", "") or "").lower()

        is_under_sink_organizer = (
            "under sink" in normalized
            and "organ" in product_idea_name
            and "sous-évier" in product_idea_name
        )

        if is_under_sink_organizer:
            parts = ["Organisateur sous-évier"]
            if "wheel" in normalized:
                parts.append("à roulettes")
            return " ".join(parts)

        product_idea = getattr(getattr(opportunity, "supplier_offer", None), "product_idea", None)
        product_idea_name = (getattr(product_idea, "name", "") or "").lower()

        is_under_sink_organizer = (
            "under sink" in normalized
            and "organ" in product_idea_name
            and "sous-évier" in product_idea_name
        )

        if is_under_sink_organizer:
            parts = ["Organisateur sous-évier"]
            if "wheel" in normalized:
                parts.append("à roulettes")
            return " ".join(parts)

        is_makeup_storage = (
            "makeup" in normalized
            and "storage" in normalized
            and "box" in normalized
        )

        if is_makeup_storage:
            parts = ["Boîte de rangement maquillage"]
            if "led" in normalized or "light mirror" in normalized:
                parts.append("avec miroir LED")
            return " ".join(parts)

        is_bike_light = (
            ("bike" in normalized or "bicycle" in normalized)
            and ("light" in normalized or "headlight" in normalized)
        )

        if is_bike_light:
            parts = ["Éclairage vélo"]

            if "rechargeable" in normalized or "usb charging" in normalized:
                parts.append("rechargeable")

            return " ".join(parts)

        if "snuffle" in normalized and "mat" in normalized and "tapis de fouille" in product_idea_name:
            parts = ["Tapis de fouille"]
            if "sunflower" in normalized:
                parts.append("tournesol")
            parts.append("pour chien")
            features = []
            if "washable" in normalized:
                features.append("lavable")
            if "slow feeding" in normalized:
                features.append("anti-glouton")
            return " ".join(parts) + (" - " + " et ".join(features) if features else "")
        return name
