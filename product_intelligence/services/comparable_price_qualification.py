from urllib.parse import (
    urlsplit,
    urlunsplit,
)
import re
import unicodedata

from product_intelligence.services.product_comparability_attributes import (
    ProductComparabilityAttributesService,
)


class ComparablePriceQualificationService:

    RETAINED_REASON = (
        "Produit comparable et données indispensables présentes."
    )

    attributes_service = ProductComparabilityAttributesService()

    @classmethod
    def qualify(
        cls,
        supplier_offer,
        collection_batch_id=None,
    ):
        examined = 0
        retained = 0
        rejected = 0
        observed_urls = set()

        comparable_prices = (
            supplier_offer
            .comparable_prices
            .all()
            .order_by("id")
        )
        if collection_batch_id is None:
            comparable_prices = comparable_prices.filter(is_current=True)

        if collection_batch_id is not None:
            comparable_prices = comparable_prices.filter(collection_batch_id=collection_batch_id)

        for comparable_price in comparable_prices:
            examined += 1

            rejection_reason = (
                cls._get_rejection_reason(
                    comparable_price,
                    supplier_offer,
                )
            )

            if not rejection_reason:
                normalized_url = (
                    cls._normalize_source_url(
                        comparable_price.source_url
                    )
                )

                if normalized_url in observed_urls:
                    rejection_reason = (
                        "Source déjà observée."
                    )
                else:
                    observed_urls.add(
                        normalized_url
                    )

            if rejection_reason:
                comparable_price.qualification_status = (
                    "rejected"
                )

                comparable_price.qualification_reason = (
                    rejection_reason
                )

                rejected += 1
            else:
                comparable_price.qualification_status = (
                    "retained"
                )

                comparable_price.qualification_reason = (
                    cls.RETAINED_REASON
                )

                retained += 1

            comparable_price.save(
                update_fields=[
                    "qualification_status",
                    "qualification_reason",
                ]
            )

        return {
            "examined": examined,
            "retained": retained,
            "rejected": rejected,
        }

    @classmethod
    def _get_rejection_reason(
        cls,
        comparable_price,
        supplier_offer=None,
    ):
        if comparable_price.observed_price <= 0:
            return "Prix non positif."

        if not comparable_price.product_name.strip():
            return "Nom du produit manquant."

        if not comparable_price.currency.strip():
            return "Devise manquante."

        if len(
            comparable_price.currency.strip()
        ) != 3:
            return "Code devise invalide."

        if not comparable_price.source_title.strip():
            return "Titre de source manquant."

        if not comparable_price.source_url.strip():
            return "URL de source manquante."

        if not comparable_price.evidence.strip():
            return "Preuve de comparabilité manquante."

        if supplier_offer is not None:
            functional_reason = (
                cls._get_functional_rejection_reason(
                    supplier_offer=supplier_offer,
                    comparable_price=comparable_price,
                )
            )
            if functional_reason:
                return functional_reason

            target = cls.attributes_service.extract(
                name=supplier_offer.product_name,
                persisted_features=supplier_offer.variant_features,
            )
            candidate = cls.attributes_service.extract(
                name=comparable_price.product_name,
                evidence=(
                    f"{comparable_price.source_title} "
                    f"{comparable_price.evidence}"
                ),
            )

            target_quantity = target["pack_quantity"]
            candidate_quantity = candidate["pack_quantity"]
            if target_quantity and target_quantity > 1:
                if candidate_quantity is None:
                    return (
                        "Contrôle requis : quantité du comparable "
                        "non vérifiable."
                    )
                if candidate_quantity != target_quantity:
                    return (
                        "Quantité différente : "
                        f"offre fournisseur {target_quantity}, "
                        f"comparable {candidate_quantity}."
                    )

            for field, label in (
                ("dimensions_mm", "Dimensions"),
                ("capacity_ml", "Capacité"),
                ("size", "Taille"),
            ):
                target_value = target[field]
                candidate_value = candidate[field]
                if (
                    target_value is not None
                    and candidate_value is not None
                    and target_value != candidate_value
                ):
                    return f"{label} différente de la variante fournisseur."

        return ""

    @staticmethod
    def _normalize_text(value):
        normalized = unicodedata.normalize(
            "NFKD", str(value or "")
        ).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(
            r"[^a-z0-9]+", " ", normalized.lower()
        )
        return " ".join(normalized.split())

    @classmethod
    def _get_functional_rejection_reason(
        cls,
        supplier_offer,
        comparable_price,
    ):
        target = cls._normalize_text(
            supplier_offer.product_name
        )
        candidate = cls._normalize_text(
            " ".join(
                (
                    comparable_price.product_name,
                    comparable_price.source_title,
                    comparable_price.evidence,
                )
            )
        )

        persisted = supplier_offer.variant_features or {}
        if (
            persisted.get("product_family") == "macrame_hanger"
            and persisted.get("includes_pot") is False
        ):
            pot_included_terms = (
                "with pot",
                "pot included",
                "avec pot",
                "pot inclus",
                "comprenant la suspension en macrame et le pot",
            )
            if any(term in candidate for term in pot_included_terms):
                return "Famille differente : ce comparable inclut le pot."

        pot_terms = (
            "planter", "flower pot", "plant pot",
            "jardiniere", "pot ", "maceta", "macetero",
        )
        hanging_terms = (
            "hanging", "suspendu", "suspendue",
            "colgante", "suspension",
        )
        target_is_hanging_pot = (
            any(term in target for term in pot_terms)
            and any(term in target for term in hanging_terms)
        )
        if not target_is_hanging_pot:
            return ""

        if not any(term in candidate for term in pot_terms):
            return "Famille différente : ce comparable n’est pas un pot."
        if not any(term in candidate for term in hanging_terms):
            return "Fixation différente : le pot comparable n’est pas suspendu."

        wall_terms = ("wall", "mural", "murale", "pared")
        target_is_wall_mounted = any(
            term in target for term in wall_terms
        )
        candidate_is_wall_mounted = any(
            term in candidate for term in wall_terms
        )
        if candidate_is_wall_mounted != target_is_wall_mounted:
            return "Fixation différente : suspension murale non comparable."

        automatic_watering_terms = (
            "self watering",
            "auto watering",
            "automatic watering",
            "auto arrosage",
            "auto arrosant",
            "auto arrosante",
            "absorcion de agua automatico",
            "deposito de agua",
            "water reservoir",
        )
        target_is_self_watering = any(
            term in target
            for term in automatic_watering_terms
        )
        candidate_is_self_watering = any(
            term in candidate
            for term in automatic_watering_terms
        )
        if candidate_is_self_watering != target_is_self_watering:
            return "Fonction différente : système d’auto-arrosage non comparable."

        return ""

    @staticmethod
    def _normalize_source_url(
        source_url,
    ):
        parsed_url = urlsplit(
            source_url.strip()
        )

        normalized_path = (
            parsed_url.path.rstrip("/")
            or "/"
        )

        return urlunsplit(
            (
                parsed_url.scheme.lower(),
                parsed_url.netloc.lower(),
                normalized_path,
                "",
                "",
            )
        )
